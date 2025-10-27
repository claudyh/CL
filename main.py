# pip install SPARQLWrapper pandas

from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

ENDPOINT = "https://query.wikidata.org/sparql"

def list_portuguese_monarchs() -> pd.DataFrame:
  query = """
  PREFIX wd:   <http://www.wikidata.org/entity/>
  PREFIX p:    <http://www.wikidata.org/prop/>
  PREFIX ps:   <http://www.wikidata.org/prop/statement/>
  PREFIX pq:   <http://www.wikidata.org/prop/qualifier/>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

  SELECT ?person ?personLabel ?positionLabel ?start ?end
  WHERE {
    ?person p:P39 ?stmt .
    ?stmt ps:P39 ?position .
    VALUES ?position { wd:Q58800860 }  # King or Queen of Portugal
    OPTIONAL { ?stmt pq:P580 ?start . }
    OPTIONAL { ?stmt pq:P582 ?end . }

    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  }
  ORDER BY ?start
  """

  sp = SPARQLWrapper(ENDPOINT)
  sp.setQuery(query)
  sp.setReturnFormat(JSON)
  sp.addCustomHttpHeader("User-Agent", "ChronoGraph/0.1 (academic; contact: you@example.com)")
  res = sp.query().convert()

  rows = []
  for b in res["results"]["bindings"]:
    rows.append({
      "person": b["personLabel"]["value"],
      "position": b["positionLabel"]["value"],
      "start": b.get("start", {}).get("value"),
      "end": b.get("end", {}).get("value"),
    })
  return pd.DataFrame(rows)

if __name__ == "__main__":
  df = list_portuguese_monarchs()
  if not df.empty:
    df["start_year"] = df["start"].apply(lambda x: int(x[:4]) if x else None)
    df["end_year"] = df["end"].apply(lambda x: int(x[:4]) if x else None)
  print(df)
  print(f"\nTotal monarchs found: {len(df)}")