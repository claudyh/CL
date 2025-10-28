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
  res = sp.query().convert()

  # Store as a triplet with temporal qualifiers
  rows = []
  
  for b in res["results"]["bindings"]:
    
    subject = b["personLabel"]["value"]
    predicate = 'heldPosition'
    obj = b["positionLabel"]["value"]
    start = b.get("start", {}).get("value")
    end = b.get("end", {}).get("value")
    
    rows.append({
      'subject': subject,
      'predicate': predicate,
      'object': obj,
      'start_date': start.split("T")[0],
      'end_date': end.split("T")[0]
    })
  
  return pd.DataFrame(rows)

if __name__ == "__main__":
  df = list_portuguese_monarchs()
  print(df)
  print(f"\nTotal monarchs found: {len(df)}")

  # Save dataset
  df.to_csv("data/portuguese_monarchs.csv", index=False)