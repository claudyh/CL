import os
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

from rdflib import Graph, Namespace
from rdflib.namespace import RDF

from src.common import label, to_date, overlaps_year
from src.common.models import CsvSourceConfig
from src.rag.retriever import build_source, filter_source_data
from src.agents.planner import parse_plan
from src.agents.answerer import answer as answer_pretty

# ---------------------------------------------------------------------
# RDF / Knowledge graph config (your existing stuff)
# ---------------------------------------------------------------------

TTL_PATH = os.environ.get("TTL_PATH", "data/portuguese_monarchs.ttl")
EX_NS = "http://example.org/portuguese_monarchs/"

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

g = Graph()
EX = Namespace(EX_NS)
g.bind("ex", EX)

if not os.path.exists(TTL_PATH):
  raise SystemExit(f"❌ Could not find {TTL_PATH}. Make sure you generated the TTL file.")

g.parse(TTL_PATH, format="turtle")
print(f"✅ Loaded RDF graph with {len(g)} triples from {TTL_PATH}")


def _iter_tenures():
  """Yield dicts for each ex:Tenure (kept for /graph/<year>)."""
  for t in g.subjects(RDF.type, EX.Tenure):
    person = next(g.objects(t, EX.person), None)
    position = next(g.objects(t, EX.position), None)
    start = next(g.objects(t, EX.startDate), None)
    end = next(g.objects(t, EX.endDate), None)
    yield {
      "tenure": t,
      "person": person,
      "person_label": label(g, person) if person else None,
      "position": position,
      "position_label": label(g, position) if position else None,
      "start_lit": start,
      "end_lit": end,
      "start": to_date(start),
      "end": to_date(end),
    }


@app.get("/graph/<int:year>")
def api_graph_year(year: int):
  """
  Return ALL dated subjects active in `year` as a graph where every edge targets 'Portugal'.
  Node types are inferred from rdf:type; labels prefer rdfs:label.
  """
  nodes = {
    "Portugal": {"id": "Portugal", "label": "Portugal", "type": "Country"}
  }
  edges = []

  for t in _iter_tenures():
    if not overlaps_year(t["start"], t["end"], year):
      continue
    subj = t["person_label"] or "Unknown"
    if subj not in nodes:
      nodes[subj] = {"id": subj, "label": subj, "type": "Person"}
    edges.append({
      "source": subj,
      "target": "Portugal",
      "label": "isMonarchOf",
    })

  return jsonify({"nodes": list(nodes.values()), "edges": edges})


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


# ---------------------------------------------------------------------
# Static / health
# ---------------------------------------------------------------------

@app.get("/")
def index():
  return "Backend running.", 200

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)