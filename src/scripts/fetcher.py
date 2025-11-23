from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
from src.common.store_triplets import store_triplets


ENDPOINT = "https://query.wikidata.org/sparql"

def get_query(name: str, query: str) -> pd.DataFrame:
  _query = f"""
  PREFIX wd:   <http://www.wikidata.org/entity/>
  PREFIX wdt:  <http://www.wikidata.org/prop/direct/>
  PREFIX p:    <http://www.wikidata.org/prop/>
  PREFIX ps:   <http://www.wikidata.org/prop/statement/>
  PREFIX pq:   <http://www.wikidata.org/prop/qualifier/>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  PREFIX schema: <http://schema.org/>
  PREFIX dct: <http://purl.org/dc/terms/>

  {query}
  """

  sp = SPARQLWrapper(ENDPOINT)
  sp.setQuery(_query)
  sp.setReturnFormat(JSON)
  sp.addCustomHttpHeader("User-Agent", "WikidataFetcher/1.0 (https://example.com;)")
  res = sp.query().convert()
  print(res)

  print(f"\nTotal {name} found: {len(res['results']['bindings'])}\n")
  store_triplets(res, f"data/{name}.csv")

  return res


QUERY_PORTUGUESE_MONARCHS = """
SELECT ?subject ?predicate ?object ?start_date ?end_date
WHERE {
  ?person p:P39 ?stmt .
  ?stmt ps:P39 ?position .
  VALUES ?position { wd:Q58800860 }  # King or Queen of Portugal
  OPTIONAL { ?stmt pq:P580 ?start . }
  OPTIONAL { ?stmt pq:P582 ?end . }

  ?person rdfs:label ?personLabel .
  FILTER (LANG(?personLabel) = "pt")

  ?position rdfs:label ?positionLabel .
  FILTER (LANG(?positionLabel) = "en")

  # Canonical projection
  BIND(?personLabel AS ?subject)
  BIND("heldPosition" AS ?predicate)
  BIND(?positionLabel AS ?object)
  BIND(?start AS ?start_date)
  BIND(?end AS ?end_date)
}
ORDER BY ?start
"""


QUERY_PORTUGUESE_BATTLES = """
SELECT DISTINCT ?subject ?predicate ?object ?start_date ?end_date
WHERE {
  VALUES ?portugalEntity {
    wd:Q45      # Portugal
    wd:Q45670   # Kingdom of Portugal
    wd:Q200464  # Portuguese Empire
  }

  # Any kind of military conflict
  ?conflict wdt:P31 ?conflictType .
  ?conflictType wdt:P279* wd:Q180684 .  # subclass of "military conflict"

  # Conflicts involving Portugal (either direction)
  {
    ?conflict wdt:P710 ?portugalEntity .
  }
  UNION
  {
    ?portugalEntity wdt:P1344 ?conflict .
  }

  # Time information – keep only literal values (dates)
  OPTIONAL {
    ?conflict wdt:P580 ?startTime .     # start time
    FILTER(isLiteral(?startTime))
  }
  OPTIONAL {
    ?conflict wdt:P582 ?endTime .       # end time
    FILTER(isLiteral(?endTime))
  }
  OPTIONAL {
    ?conflict wdt:P585 ?pointInTime .   # point in time (single battles)
    FILTER(isLiteral(?pointInTime))
  }

  # Choose best available value
  BIND( COALESCE(?startTime, ?pointInTime) AS ?startRaw )
  FILTER(BOUND(?startRaw) && isLiteral(?startRaw))   # ensure it's really a literal

  BIND( COALESCE(?endTime, ?startRaw) AS ?endRaw )

  # Labels
  ?conflict rdfs:label ?conflictLabel .
  FILTER (LANG(?conflictLabel) = "en")

  ?portugalEntity rdfs:label ?portugalLabel .
  FILTER (LANG(?portugalLabel) = "en")

  # Project as subject / predicate / object
  BIND(?conflictLabel AS ?subject)
  BIND("participant" AS ?predicate)   # relation label as plain text
  BIND(?portugalLabel AS ?object)

  # Dates as YYYY-MM-DD strings
  BIND( SUBSTR(STR(?startRaw), 1, 10) AS ?start_date )
  BIND( SUBSTR(STR(?endRaw),   1, 10) AS ?end_date )
}
ORDER BY ?start_date
"""


if __name__ == "__main__":
  get_query("portuguese_monarchs", QUERY_PORTUGUESE_MONARCHS)
  get_query("portuguese_battles", QUERY_PORTUGUESE_BATTLES)