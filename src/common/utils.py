from datetime import date

from rdflib import Literal
from rdflib.namespace import RDFS

def to_date(lit: Literal):
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

def label(g, node_or_lit):
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

def overlaps_year(start_d, end_d, year: int) -> bool:
  if start_d is None and end_d is None:
    return False
  y_start = start_d.year if start_d else -10**9
  y_end = end_d.year if end_d else 10**9
  return y_start <= year <= y_end