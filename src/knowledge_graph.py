import pandas as pd
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, XSD

df = pd.read_csv("data/portuguese_monarchs.csv")

g = Graph()
EX = Namespace("http://example.org/portuguese_monarchs/")
g.bind("ex", EX)

def uriify(name):
    return URIRef(EX + name.replace(" ", "_").replace(",", ""))

for _, row in df.iterrows():
    person = uriify(row["subject"])
    position = uriify(row["object"])
    tenure = BNode()

    g.add((person, RDF.type, EX.Person))
    g.add((person, RDFS.label, Literal(row["subject"])))
    g.add((position, RDF.type, EX.Position))
    g.add((position, RDFS.label, Literal(row["object"])))
    
    g.add((tenure, RDF.type, EX.Tenure))
    g.add((tenure, EX.person, person))
    g.add((tenure, EX.position, position))
    g.add((tenure, EX.startDate, Literal(row["start_date"], datatype=XSD.date)))
    g.add((tenure, EX.endDate, Literal(row["end_date"], datatype=XSD.date)))

g.serialize("data/portuguese_monarchs.ttl", format="turtle")
print("RDF graph written to data/portuguese_monarchs.ttl")


# How to fetch the data:
# “Who was monarch on January 1st, 1500?”
from rdflib.plugins.sparql import prepareQuery

q = prepareQuery("""
SELECT ?person ?start ?end
WHERE {
  ?t a ex:Tenure ;
     ex:person ?person ;
     ex:startDate ?start ;
     ex:endDate ?end .
  FILTER("1500-01-01"^^xsd:date >= ?start && "1500-01-01"^^xsd:date <= ?end)
}
""", initNs={"ex": EX, "xsd": XSD})

for row in g.query(q):
    print(row.person, row.start, row.end)


# Visualize the graph
from pyvis.network import Network

# Create an interactive graph
net = Network(height="800px", width="100%", notebook=False, directed=True)
net.force_atlas_2based()  # prettier layout

for s, p, o in g:
    # Add nodes
    net.add_node(str(s), label=str(s).split('/')[-1], color="#8ecae6")
    net.add_node(str(o), label=str(o).split('/')[-1], color="#ffb703")
    # Add edge
    net.add_edge(str(s), str(o), label=str(p).split('/')[-1])

net.write_html("portuguese_monarchs_graph.html", open_browser=True)
print("Graph saved to 'portuguese_monarchs_graph.html' — open it in a browser!")
