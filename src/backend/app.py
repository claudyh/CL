import os
from datetime import date
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from rdflib import Graph, Namespace, Literal, URIRef
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

# ---------------- Helpers ----------------

def _to_date(lit: Literal):
    """Parse xsd:date or date-like literal to python date. Falls back to YYYY-01-01 for year-only."""
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

def _label(node_or_lit):
    """Prefer rdfs:label; else last path segment (for URIs); else string form."""
    if isinstance(node_or_lit, Literal):
        return str(node_or_lit)
    lbl = next(g.objects(node_or_lit, RDFS.label), None)
    if lbl:
        return str(lbl)
    try:
        return str(node_or_lit).split("/")[-1].replace("_", " ")
    except Exception:
        return str(node_or_lit)

def _first_type_localname(node: URIRef):
    """Return the first rdf:type localname (e.g., 'Tenure', 'Event') if available."""
    for t in g.objects(node, RDF.type):
        t_str = str(t)
        local = t_str.split("#")[-1].split("/")[-1]
        return local
    return None

def _active_interval(start_lit: Literal, end_lit: Literal):
    """Return (start_date, end_date) as python dates (None allowed)."""
    return _to_date(start_lit), _to_date(end_lit)

def _overlaps_year(start_d, end_d, year: int) -> bool:
    if start_d is None and end_d is None:
        return False
    y_start = start_d.year if start_d else -10**9
    y_end = end_d.year if end_d else 10**9
    return y_start <= year <= y_end

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
            "person_label": _label(person) if person else None,
            "position": position,
            "position_label": _label(position) if position else None,
            "start_lit": start,
            "end_lit": end,
            "start": _to_date(start),
            "end": _to_date(end),
        }

def _looks_like_portugal(value) -> bool:
    """Heuristic: does a node/literal label mention Portugal (case-insensitive) or equal 'Portugal'."""
    if value is None:
        return False
    txt = _label(value).strip()
    return txt.lower() == "portugal" or "portugal" in txt.lower()

def _infer_edge_label_for_subject(s: URIRef) -> str:
    """
    Heuristic to choose edge label from subject->Portugal.
    - If it's a Tenure or has ex:person + ex:position with 'Portugal' ⇒ isMonarchOf
    - If looks like an Event or has ex:country/ex:location mentioning Portugal ⇒ occursIn
    - Else ⇒ relatedTo
    """
    typ = _first_type_localname(s)
    person = next(g.objects(s, EX.person), None)
    position = next(g.objects(s, EX.position), None)
    country = next(g.objects(s, EX.country), None)
    location = next(g.objects(s, EX.location), None)

    if typ == "Tenure" or (person and position and _looks_like_portugal(position)):
        return "isMonarchOf"
    if typ in ("Event", "Battle", "Treaty") or _looks_like_portugal(country) or _looks_like_portugal(location):
        return "occursIn"
    return "relatedTo"

def _iter_dated_subjects():
    """
    Iterate all subjects that have ex:startDate and/or ex:endDate, returning a dict:
    { 's': subject, 'label': str, 'type': localname|None, 'start_lit', 'end_lit', 'start', 'end' }
    """
    seen = set()
    # subjects with startDate or endDate
    for s in set(list(g.subjects(EX.startDate, None)) + list(g.subjects(EX.endDate, None))):
        if s in seen:
            continue
        seen.add(s)
        start_lit = next(g.objects(s, EX.startDate), None)
        end_lit = next(g.objects(s, EX.endDate), None)
        start_d, end_d = _active_interval(start_lit, end_lit)
        yield {
            "s": s,
            "label": _label(s),
            "type": _first_type_localname(s),
            "start_lit": start_lit,
            "end_lit": end_lit,
            "start": start_d,
            "end": end_d,
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

    # 1) Include monarch tenures as Person -> Portugal (isMonarchOf)
    for t in _iter_tenures():
        if not _overlaps_year(t["start"], t["end"], year):
            continue
        subj = t["person_label"] or "Unknown"
        if subj not in nodes:
            nodes[subj] = {"id": subj, "label": subj, "type": "Person"}
        edges.append({
            "source": subj,
            "target": "Portugal",
            "label": "isMonarchOf",
            "start_date": str(t["start_lit"]) if t["start_lit"] else None,
            "end_date": str(t["end_lit"]) if t["end_lit"] else None,
        })

    # 2) Include ANY other dated subjects active in the year -> Portugal (occursIn / relatedTo)
    for item in _iter_dated_subjects():
        s_node = item["s"]
        # Skip Tenure nodes themselves to avoid duplicate concept-edges; we handled via the Person above.
        if _first_type_localname(s_node) == "Tenure":
            continue

        if not _overlaps_year(item["start"], item["end"], year):
            continue

        subj_label = item["label"] or "Unknown"
        subj_type = item["type"] or "Thing"

        if subj_label not in nodes:
            nodes[subj_label] = {"id": subj_label, "label": subj_label, "type": subj_type}

        predicate = _infer_edge_label_for_subject(s_node)
        edges.append({
            "source": subj_label,
            "target": "Portugal",
            "label": predicate,
            "start_date": str(item["start_lit"]) if item["start_lit"] else None,
            "end_date": str(item["end_lit"]) if item["end_lit"] else None,
        })

    return jsonify({"nodes": list(nodes.values()), "edges": edges})

# ---------------- Static ----------------

@app.get("/")
def index():
    try:
        return send_from_directory(app.static_folder, "index.html")
    except Exception:
        return "Backend running. Build your frontend and place it in /static to serve here.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)