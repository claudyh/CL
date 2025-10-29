from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
from src.common.store_triplets import store_triplets

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
  
  return res


if __name__ == "__main__":
  result = list_portuguese_monarchs()
  print(result)
  print(f"\nTotal monarchs found: {len(result)}")

  # Save dataset
  store_triplets(result, "data/portuguese_monarchs.csv")