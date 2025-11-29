import os
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

from rdflib import XSD, Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
from rdflib.plugins.sparql import prepareQuery

from src.common import label, to_date, overlaps_year
from src.common.models import CsvSourceConfig
from src.rag.retriever import build_source, filter_source_data
from src.agents.planner import parse_plan
from src.agents.answerer import answer as answer_pretty
from src.llm import get_answers

# ---------------------------------------------------------------------
# RDF / Knowledge graph config (your existing stuff)
# ---------------------------------------------------------------------

TTL_PATH = os.environ.get("TTL_PATH", "data/portuguese_knowledge_graph.ttl")
EX_NS = "http://example.org/portuguese/"

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

g = Graph()
EX = Namespace(EX_NS)
g.bind("ex", EX)

if not os.path.exists(TTL_PATH):
  raise SystemExit(f"❌ Could not find {TTL_PATH}. Make sure you generated the TTL file.")

g.parse(TTL_PATH, format="turtle")
print(f"✅ Loaded RDF graph with {len(g)} triples from {TTL_PATH}")


@app.get("/graph/<int:year>")
def api_graph_year(year: int):
    """
    Return all RDF subjects active in `year`,
    using your new structure:
        event → (ex:subject, ex:object, ex:startDate, ex:endDate)
    """
    year_lit = Literal(f"{year}-01-01", datatype=XSD.date)

    nodes = {
        "Portugal": {
            "id": "Portugal",
            "label": "Portugal",
            "type": "Country"
        }
    }
    edges = []

    q = prepareQuery("""
    SELECT ?event ?subject ?object ?start ?end
    WHERE {
      ?event a ex:Event ;
             ex:subject ?subject ;
             ex:object ?object ;
             ex:startDate ?start ;
             ex:endDate ?end .
      FILTER (?start <= ?date && ?end >= ?date)
    }
    """, initNs={"ex": EX, "xsd": XSD})

    # Query RDF
    rows = g.query(q, initBindings={"date": year_lit})

    for row in rows:
        subject = row.subject
        object_ = row.object

        # Find relation: ex:monarch / ex:battle / ex:treaty ...
        relation = None
        for p in g.predicates(subject=subject, object=object_):
            if str(p).startswith(str(EX)):
                relation = p
                break

        if relation is None:
            continue

        rel_name = str(relation).split("/")[-1]

        # Subject label
        label_val = next(g.objects(subject, RDFS.label), None)
        label_str = str(label_val) if label_val else subject.split("/")[-1]

        # Infer type
        subj_type = "Person" if "monarch" in rel_name else "Event"

        # Add node
        if label_str not in nodes:
            nodes[label_str] = {
                "id": label_str,
                "label": label_str,
                "type": subj_type
            }

        # Add edge
        edges.append({
            "source": label_str,
            "target": "Portugal",
            "label": rel_name
        })

    print(f"[{year}] Nodes: {len(nodes)}  Edges: {len(edges)}")

    return jsonify({
        "year": year,
        "nodes": list(nodes.values()),
        "edges": edges
    })


@app.get("/node/<name>")
def api_node_details(name: str):
    """
    Return detailed info for a given node by rdfs:label,
    correctly fetching relations and dates from associated event BNodes.
    """
    # Find node by rdfs:label
    node_uri = None
    for s, label_val in g.subject_objects(RDFS.label):
        if str(label_val) == name:
            node_uri = s
            break

    if not node_uri:
        return jsonify({"error": f"Node '{name}' not found"}), 404

    label_str = name

    # Node type
    type_val = next(g.objects(node_uri, RDF.type), None)
    type_str = str(type_val).split("/")[-1] if type_val else "Unknown"

    # Initialize
    relations = []
    start = end = None

    # Look for events where node is subject
    for event in g.subjects(EX.subject, node_uri):
        obj = next(g.objects(event, EX.object), None)
        if obj:
            obj_label = next(g.objects(obj, RDFS.label), None)
            obj_label_str = str(obj_label) if obj_label else str(obj).split("/")[-1]

            # Find the predicate from node -> object
            pred = None
            for p in g.predicates(node_uri, obj):
                if str(p).startswith(str(EX)):
                    pred = str(p).split("/")[-1]
                    break
            if not pred:
                # fallback: use rdf:type mapping
                pred = "relatedTo"

            relations.append({
                "predicate": pred,
                "object": obj_label_str
            })

        start_val = next(g.objects(event, EX.startDate), None)
        end_val = next(g.objects(event, EX.endDate), None)
        if start_val:
            start = str(start_val)
        if end_val:
            end = str(end_val)

        break  # pick first event for simplicity
      
    print(f"AAAAAAA [Node] {label_str}: Type={type_str}, Relations={len(relations)}, Start={start}, End={end}")

    return jsonify({
        "id": str(node_uri),
        "label": label_str,
        "type": type_str,
        "relations": relations,
        "start": start,
        "end": end
    })


# ---------------------------------------------------------------------
# Agent / CSV RAG config
# ---------------------------------------------------------------------

SOURCES = [
  CsvSourceConfig(
    name="monarchs",
    path="data/portuguese_monarchs.csv",
  ),
  CsvSourceConfig(
    name="battles",
    path="data/portuguese_battles.csv",
  ),
  # later: add more sources
]

# Global runtime objects initialised once at startup
VECTOR_STORE = None
SOURCE_DATA = None


print("🔧 Loading CSV sources into memory...")
SOURCE_DATA = build_source(SOURCES)


def run_agent(question: str) -> dict:
  """
  Core pipeline:
    question -> plan -> (RAG or CSV filter) -> answer
  Returns a dict ready to jsonify.
  """
  plan = parse_plan(question)

  matches = filter_source_data(SOURCE_DATA, plan)
  answer_text = answer_pretty(question, matches)

  return {
    "question": question,
    "plan": plan.model_dump(),
    "answer": answer_text,
    "matches": [d.model_dump() for d in matches],
  }


# ---------------------------------------------------------------------
# API endpoint to talk to your agent
# ---------------------------------------------------------------------
'''
@app.post("/ask")
def api_ask():
  """
  POST /ask
  JSON body: { "question": "..." }

  Response:
  {
    "question": "...",
    "plan": { ... },
    "answer": "...",
    "matches": [ ... ]
  }
  """
  try:
    data = request.get_json(force=True, silent=True) or {}
    question = data.get("question")

    if not question or not isinstance(question, str):
      return jsonify({"error": "Field 'question' (string) is required"}), 400

    result = run_agent(question)
    return jsonify(result), 200

  except Exception as e:
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500
'''


@app.post("/ask")
def api_ask():
  data = request.get_json(force=True)
  question = data.get("question")
  if not question:
      return jsonify({"error": "question required"}), 400
  
  try:
    years, answers = get_answers(question)
    return jsonify({
        "years": years,
        "answers": answers
    }), 200
  except Exception as e:
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# Static / health
# ---------------------------------------------------------------------

@app.get("/")
def index():
  return "Backend running.", 200

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)