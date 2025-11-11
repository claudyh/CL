# retrieve.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re
from dataclasses import dataclass, field

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, Literal, XSD
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from common.query_plan import QueryPlan

# ---------- Config ----------
DATASET_PATH = "data/portuguese_monarchs.ttl"
PERSIST_DIR = ".chroma_rdf"
COLLECTION_NAME = "rdf_rulers"

EX = Namespace("http://example.org/portuguese_monarchs/")
RDFS_NS = RDFS

# ---------- Helpers ----------
def year_from_xsd_date(val: Literal | str) -> Optional[int]:
    """Extract int year from xsd:date 'YYYY-MM-DD' or any string with YYYY."""
    s = str(val)
    # Prefer exact xsd:date parsing if typed
    if isinstance(val, Literal) and val.datatype in (XSD.date, URIRef(str(XSD.date))):
        # val.toPython() would be a datetime.date
        try:
            py = val.toPython()
            return int(py.year)
        except Exception:
            pass
    m = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", s)
    return int(m.group(0)) if m else None

@dataclass
class PersonTenures:
    iri: str
    label: Optional[str] = None
    tenures: List[Tuple[int, int]] = field(default_factory=list)

    @property
    def min_year(self) -> Optional[int]:
        return min((a for a, _ in self.tenures), default=None)

    @property
    def max_year(self) -> Optional[int]:
        return max((b for _, b in self.tenures), default=None)

# ---------- Load RDF & build documents ----------
def build_person_docs_from_ttl(ttl_path: str) -> List[Document]:
    g = Graph()
    g.parse(ttl_path, format="turtle")

    # Collect rdfs:label for all people
    labels: Dict[str, str] = {}
    for s, p, o in g.triples((None, RDFS_NS.label, None)):
        labels[str(s)] = str(o)

    # Aggregate tenures only for the Monarch_of_Portugal position
    people: Dict[str, PersonTenures] = {}

    for tenure in g.subjects(RDF.type, EX.Tenure):
        # Tenure nodes are blank nodes in your TTL; fetch properties
        person = g.value(tenure, EX.person)
        position = g.value(tenure, EX.position)
        start = g.value(tenure, EX.startDate)
        end = g.value(tenure, EX.endDate)

        if not (person and position and start and end):
            continue
        if str(position) != str(EX.Monarch_of_Portugal):
            # If later you model more positions, keep only Monarch here
            continue

        y1, y2 = year_from_xsd_date(start), year_from_xsd_date(end)
        if not (y1 and y2):
            continue
        if y1 > y2:  # sanity
            y1, y2 = y2, y1

        p_iri = str(person)
        if p_iri not in people:
            people[p_iri] = PersonTenures(iri=p_iri, label=labels.get(p_iri))
        people[p_iri].tenures.append((y1, y2))

    # Build one doc per person with tenure summary
    docs: List[Document] = []
    for p in people.values():
        # Content: concise, but includes all tenures to help semantic search
        label = p.label or p.iri.rsplit("/", 1)[-1]
        tenures_str = "; ".join(f"{a}-{b}" for a, b in sorted(p.tenures))
        content = (
            f"Person: {label}\n"
            f"IRI: {p.iri}\n"
            f"Position: Monarch of Portugal\n"
            f"Tenures (years): {tenures_str}\n"
        )
        meta = {
            "subject": p.iri,
            "label": label,
            "position": "Monarch of Portugal",
            "tenures": p.tenures,   # stored as list of [start,end]; Chroma will JSON-encode
            "min_year": p.min_year,
            "max_year": p.max_year,
        }
        docs.append(Document(page_content=content, metadata=meta))

    return docs

# ---------- Vector store ----------
def build_or_load_vectorstore(rebuild: bool = False) -> Chroma:
    docs = build_person_docs_from_ttl(DATASET_PATH)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_documents(docs)

    emb = OllamaEmbeddings(model="nomic-embed-text")

    if rebuild and Path(PERSIST_DIR).exists():
        import shutil; shutil.rmtree(PERSIST_DIR)

    if not Path(PERSIST_DIR).exists() or rebuild:
        vs = Chroma.from_documents(
            documents=chunks,
            embedding=emb,
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME,
        )
        vs.persist()
        return vs
    else:
        return Chroma(
            embedding_function=emb,
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME,
        )

VS = build_or_load_vectorstore(rebuild=True)

# ---------- Retrieval ----------
def _year_filter_single(y: int) -> dict:
    # Keep rulers whose reign window covers the year
    return {"$and": [{"min_year": {"$lte": y}}, {"max_year": {"$gte": y}}]}

def _year_filter_range(a: int, b: int) -> dict:
    # Overlap between [min_year, max_year] and [a, b]
    return {"$and": [{"max_year": {"$gte": a}}, {"min_year": {"$lte": b}}]}

def retrieve_text(plan: QueryPlan, k: int = 6):
    synonyms = ["head of state", "monarch", "king", "queen", "ruler"]
    query = f"{plan.relation} of {plan.target}; monarch of Portugal; ruler of Portugal; " + ", ".join(synonyms)

    filt = None
    if plan.time and plan.time.start and plan.time.end:
        if plan.time.start == plan.time.end:
            filt = _year_filter_single(plan.time.start)
        else:
            a, b = sorted([plan.time.start, plan.time.end])
            filt = _year_filter_range(a, b)
    elif plan.time and plan.time.start:
        filt = _year_filter_single(plan.time.start)

    return VS.similarity_search(
          query,
          k=k,
          filter=filt
      )