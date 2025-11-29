import pandas as pd
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, XSD

# 1. Create RDF graph
g = Graph()
EX = Namespace("http://example.org/portuguese/")
g.bind("ex", EX)

PORTUGAL = URIRef(EX + "Portugal")

# Utility: Convert names into URIs
def uriify(name, prefix=EX):
    return URIRef(prefix + str(name).replace(" ", "_").replace(",", ""))

# Generic function to load a CSV into RDF
def load_csv_to_graph(csv_path, relation_name):
    """
    relation_name: str, e.g., "monarch", "battle", "treaty"
    """
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        subj = uriify(row["subject"])
        obj = PORTUGAL
        pred_uri = EX[relation_name]

        # Event node (BNode) for temporal info
        event = BNode()

        # Add subject type
        if relation_name == "monarch":
            g.add((subj, RDF.type, EX.Person))
        else:
            g.add((subj, RDF.type, EX.Event))
        g.add((subj, RDFS.label, Literal(row["subject"])))

        # Add Portugal node type if not already added
        g.add((obj, RDF.type, EX.Country))
        g.add((obj, RDFS.label, Literal("Portugal")))

        # Add the predicate from subject -> Portugal
        g.add((subj, pred_uri, obj))

        # Add temporal information via event node
        g.add((event, RDF.type, EX.Event))
        g.add((event, EX.subject, subj))
        g.add((event, EX.object, obj))
        g.add((event, EX.startDate, Literal(row["start_date"], datatype=XSD.date)))
        g.add((event, EX.endDate, Literal(row["end_date"], datatype=XSD.date)))

# Load all CSVs
csv_files = [
    ("data/portuguese_monarchs.csv", "monarch"),
    ("data/portuguese_battles.csv", "battle"),
    # ("data/portuguese_treaties.csv", "treaty"), # add more later
]

for file, relation in csv_files:
    load_csv_to_graph(file, relation)

# Save TTL
g.serialize("data/portuguese_knowledge_graph.ttl", format="turtle")
print("RDF graph written to 'data/portuguese_knowledge_graph.ttl'")

# Example SPARQL query: entities active on a specific year
from rdflib.plugins.sparql import prepareQuery

q = prepareQuery("""
SELECT ?subject ?predicate ?object ?start ?end
WHERE {
  ?event ex:subject ?subject ;
         ex:object ?object ;
         ex:startDate ?start ;
         ex:endDate ?end .
  ?subject ?predicate ?object .
  FILTER("1500-01-01"^^xsd:date >= ?start && "1500-01-01"^^xsd:date <= ?end)
}
""", initNs={"ex": EX, "xsd": XSD})

for row in g.query(q):
    print(row.subject, row.predicate, row.object, row.start, row.end)

# Visualize
from pyvis.network import Network

net = Network(height="800px", width="100%", notebook=False, directed=True)
net.force_atlas_2based()

for s, p, o in g:
    # Node colors
    color = "#60C4AB" if str(o) == str(PORTUGAL) else "#8ecae6"
    net.add_node(str(s), label=str(s).split('/')[-1], color=color)
    net.add_node(str(o), label=str(o).split('/')[-1], color=color)
    net.add_edge(str(s), str(o), label=str(p).split('/')[-1])

net.write_html("portuguese_knowledge_graph.html", open_browser=True)
print("Graph saved to 'portuguese_knowledge_graph.html'")
