import os
from flask import Flask, jsonify
from flask_cors import CORS
from rdflib import Graph, Namespace
from rdflib.namespace import RDF
from src.common import label, to_date, overlaps_year

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

# ---------------- Helpers ----------------


def _iter_tenures():
  """Yield dicts for each ex:Tenure (kept for /api/monarchs)."""
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

# ---------------- Static ----------------

@app.get("/")
def index():
  return "Backend running.", 200

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)