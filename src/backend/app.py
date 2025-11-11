# app.py
import os
from datetime import date
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, XSD

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

def _to_date(lit: Literal):
    if not isinstance(lit, Literal):
        return None
    val = str(lit)
    try:
        y, m, d = val[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        try:
            return date(int(val[:4]), 1, 1)
        except Exception:
            return None

def _label(node):
    lbl = next(g.objects(node, RDFS.label), None)
    return str(lbl) if lbl else str(node).split("/")[-1].replace("_", " ")

def _iter_tenures():
    for t in g.subjects(RDF.type, EX.Tenure):
        person = next(g.objects(t, EX.person), None)
        position = next(g.objects(t, EX.position), None)
        start = next(g.objects(t, EX.startDate), None)
        end = next(g.objects(t, EX.endDate), None)
        yield {
            "tenure": t,
            "person": person,
            "person_label": _label(person) if person else None,
            "position": position,
            "position_label": _label(position) if position else None,
            "start_lit": start,
            "end_lit": end,
            "start": _to_date(start),
            "end": _to_date(end),
        }

def _active_in_year(tenure, year: int) -> bool:
    if tenure["start"] is None and tenure["end"] is None:
        return False
    y_start = tenure["start"].year if tenure["start"] else -10**9
    y_end = tenure["end"].year if tenure["end"] else 10**9
    return y_start <= year <= y_end

@app.get("/api/years")
def api_years():
    years = []
    for t in _iter_tenures():
        if t["start"]:
            years.append(t["start"].year)
        if t["end"]:
            years.append(t["end"].year)
    if not years:
        return jsonify({"min": None, "max": None})
    return jsonify({"min": min(years), "max": max(years)})

@app.get("/api/monarchs")
def api_monarchs():
    year_str = request.args.get("year")
    if not year_str or not year_str.isdigit():
        return jsonify({"error": "Provide ?year=YYYY"}), 400
    year = int(year_str)

    triples = []
    for t in _iter_tenures():
        if not _active_in_year(t, year):
            continue
        obj_label = "Portugal" if ("portugal" in (t["position_label"] or "").lower()) else t["position_label"]
        triples.append({
            "subject": t["person_label"],
            "predicate": "isMonarchOf" if obj_label == "Portugal" else "holdsPosition",
            "object": obj_label,
            "start_date": str(t["start_lit"]) if t["start_lit"] else None,
            "end_date": str(t["end_lit"]) if t["end_lit"] else None,
        })

    nodes = {}
    edges = []
    nodes["Portugal"] = {"id": "Portugal", "label": "Portugal", "type": "Country"}

    for tr in triples:
        s = tr["subject"]
        o = tr["object"] or "Unknown"
        if s not in nodes:
            nodes[s] = {"id": s, "label": s, "type": "Person"}
        if o not in nodes:
            nodes[o] = {"id": o, "label": o, "type": "Position" if o != "Portugal" else "Country"}
        edges.append({
            "source": s,
            "target": o,
            "label": tr["predicate"],
            "start_date": tr["start_date"],
            "end_date": tr["end_date"],
        })

    return jsonify({
        "year": year,
        "triples": triples,
        "graph": {"nodes": list(nodes.values()), "edges": edges}
    })

# NEW: a route that matches your frontend call and returns the shape it expects
@app.get("/graph/<int:year>")
def api_graph_year(year: int):
    # Reuse the logic via internal call to /api/monarchs
    with app.test_request_context(f"/api/monarchs?year={year}"):
        resp = api_monarchs()
        # api_monarchs returns (json, status) on error; handle both shapes:
        if isinstance(resp, tuple):
            payload, status = resp
            return payload, status
        data = resp.get_json()
    return jsonify({
        "nodes": data["graph"]["nodes"],
        "edges": data["graph"]["edges"]
    })

@app.get("/")
def index():
    # serve UI if present
    try:
        return send_from_directory(app.static_folder, "index.html")
    except Exception:
        return "Backend running. Build your frontend and place it in /static to serve here.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)