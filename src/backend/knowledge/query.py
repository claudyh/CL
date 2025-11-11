from rdflib import Graph

g = Graph()
g.parse("data/portuguese_monarchs.ttl", format="turtle")

def triples_for_year(year):
    query = f"""
    PREFIX ex: <http://example.org/portuguese_monarchs/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?person ?position ?start ?end WHERE {{
      ?t a ex:Tenure ;
         ex:person ?person ;
         ex:position ?position ;
         ex:startDate ?start ;
         ex:endDate ?end .
      FILTER("{year}-01-01"^^xsd:date >= ?start &&
             "{year}-01-01"^^xsd:date <= ?end)
    }}
    """

    results = g.query(query)

    nodes = set()
    edges = []

    for row in results:
        person = str(row.person).split("/")[-1]
        position = str(row.position).split("/")[-1]

        nodes.add(person)
        nodes.add(position)

        edges.append({
            "source": person,
            "target": position,
            "label": "holdsPosition"
        })

    return [{"id": n, "label": n} for n in nodes], edges