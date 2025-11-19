import pandas as pd
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, XSD


DEBUG = False



# Load the data
df = pd.read_csv("data/portuguese_monarchs.csv")

'''
[Some context]
RDF (Resource Description Framework) graph

Namespace - "Everything that can be described should have a globally
unique identifier — and the web already has a system for that: URLs."
-> so we use a URL like a URI (Uniform Resource Identifier)
Different tools can automatically merge nodes — even though they came
from different sources — because the URIs provide a shared identity.
That's the core idea of the Semantic Web and Linked Data.
'''


# 1. Create RDF graph ------------------------------------------
g = Graph()
EX = Namespace("http://example.org/portuguese_monarchs/")

# Bind - tells RDFLib to include this prefix in the output.
g.bind("ex", EX)

# Function to turn names into URIs
def uriify(name):
    return URIRef(EX + name.replace(" ", "_").replace(",", ""))

# Populate the graph
for _, row in df.iterrows():
    person = uriify(row["subject"]) # URI for the monarch
    position = uriify(row["object"]) # URI for the position
    
    # [Tenure] - a node that represents the fact itself
    # (since we dont just have tiplets - but time qualifiers as well)
    # It is an “event object” that ties everything together, and since its
    # unique and doesn’t need to be referenced elsewhere we use a blank node
    tenure = BNode()


    # Add triples (subject, predicate, object)
    g.add((person, RDF.type, EX.Person)) # (ex: Manuel_II,  rdf: type,  ex: Person)
    g.add((person, RDFS.label, Literal(row["subject"]))) # (ex: Manuel_II,  rdf: label,  ex: "Manuel II")
    g.add((position, RDF.type, EX.Position)) # (ex: Monarch_of_Pt,  rdf: type,  ex: Position)
    g.add((position, RDFS.label, Literal(row["object"]))) # (ex: Monarch_of_Pt,  rdf: label,  ex: "Monarch of Pt")
    
    g.add((tenure, RDF.type, EX.Tenure)) # ( _:b0,  rdf: type,  ex: Tenure)
    g.add((tenure, EX.person, person)) # ( _:b0,  ex: person,  ex: Manuel_II)
    g.add((tenure, EX.position, position)) # ( _:b0,  ex: position,  ex: Monarch_of_Pt)
    g.add((tenure, EX.startDate, Literal(row["start_date"], datatype=XSD.date))) # ( _:b0,  ex: startDate,  "1908-05-26")
    g.add((tenure, EX.endDate, Literal(row["end_date"], datatype=XSD.date))) # ( _:b0,  ex: endDate,  "1910-10-05")

# Write triples into Turtle (.ttl) file — human-readable RDF syntax
g.serialize("data/portuguese_monarchs.ttl", format="turtle")
print("RDF graph written to data/portuguese_monarchs.ttl")


# 2. How to fetch the data -------------------------------------
# Ex: “Who was monarch on January 1st, 1500?”
from rdflib.plugins.sparql import prepareQuery

# Prepare the query
q = prepareQuery("""
SELECT ?person ?start ?end
WHERE {
  ?t a ex:Tenure ;
     ex:person ?person ;
     ex:startDate ?start ;
     ex:endDate ?end .
  FILTER("1500-01-01"^^xsd:date >= ?start && "1500-01-01"^^xsd:date <= ?end)
}
""", initNs={"ex": EX, "xsd": XSD}) # Namespace prefixes in use: ex (custom namespace) and xsd (for dates)

# Execute the query and print all results found
for row in g.query(q):
    print(row.person, row.start, row.end)


# 3. Visualize the graph ---------------------------------------
if DEBUG:
    from pyvis.network import Network

    # Create an interactive graph
    net = Network(height="800px", width="100%", notebook=False, directed=True)
    net.force_atlas_2based()  # prettier layout

    # For each (subject, predicate, object) in graph
    for s, p, o in g:
        # Add nodes
        net.add_node(str(s), label=str(s).split('/')[-1], color="#8ecae6") # Subject - blue
        net.add_node(str(o), label=str(o).split('/')[-1], color="#ffb703") # Object - yellow
        # Add edge
        net.add_edge(str(s), str(o), label=str(p).split('/')[-1])

    # Save and open the graph in a browser
    net.write_html("portuguese_monarchs_graph.html", open_browser=True)
    print("Graph saved to 'portuguese_monarchs_graph.html' — open it in a browser!")
