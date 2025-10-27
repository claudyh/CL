# pip install SPARQLWrapper pandas

from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

ENDPOINT = "https://query.wikidata.org/sparql"

def list_portuguese_monarchs() -> pd.DataFrame:
  query = """
  PREFIX wd:   <http://www.wikidata.org/entity/>
  PREFIX wdt:  <http://www.wikidata.org/prop/direct/>
  PREFIX p:    <http://www.wikidata.org/prop/>
  PREFIX ps:   <http://www.wikidata.org/prop/statement/>
  PREFIX pq:   <http://www.wikidata.org/prop/qualifier/>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

  SELECT ?person ?personLabel ?positionLabel ?start ?end
  WHERE {
    # Find all persons with 'position held' (P39)
    ?person p:P39 ?stmt .
    ?stmt ps:P39 ?position .

    # temporal qualifiers (start/end of reign)
    OPTIONAL { ?stmt pq:P580 ?start . }
    OPTIONAL { ?stmt pq:P582 ?end . }

    # restrict to positions that are monarchs and of Portugal
    FILTER EXISTS { ?position wdt:P279* wd:Q116 } # subclass of monarch
    FILTER EXISTS {
      VALUES ?pt { wd:Q45 } # Portugal
      # { ?stmt pq:P1001 ?pt } UNION
      # { ?stmt pq:P642 ?pt } UNION
      { ?position rdfs:label ?pl .
        FILTER(LANG(?pl)="en" && CONTAINS(LCASE(?pl), "portugal"))
      }
    }

    # Remove "consort" or "spouse" positions
    FILTER NOT EXISTS {
      ?position rdfs:label ?posLabel .
      FILTER(LANG(?posLabel)="en" && REGEX(LCASE(?posLabel), "consort|spouse"))
    }

    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  }
  ORDER BY ?start
  """

  sp = SPARQLWrapper(ENDPOINT)
  sp.setQuery(query)
  sp.setReturnFormat(JSON)
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

  # optional: convert to year only
  def year(v): return int(v[:4]) if v else None
  if not df.empty:
    df["start_year"] = df["start"].map(year)
    df["end_year"] = df["end"].map(year)
  print(df.head(20))
  print(f"\nTotal monarchs found: {len(df)}")