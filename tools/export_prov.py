import sys
from rdflib import Graph, Namespace, Literal, RDF, URIRef
from rdflib.namespace import PROV, XSD

def export_to_prov(data_trace):
    """Converts OpenChokepoint trace to PROV-O Turtle format."""
    g = Graph()
    OCP = Namespace("https://openchokepoint.org/ns#")
    g.bind("prov", PROV)
    g.bind("ocp", OCP)

    for item in data_trace.get('items', []):
        subject = URIRef(OCP[item['id']])
        g.add((subject, RDF.type, PROV.Entity))
        if 'label' in item:
            g.add((subject, PROV.label, Literal(item['label'], datatype=XSD.string)))

    return g.serialize(format='turtle')

if __name__ == "__main__":
    # Minimal validation for CI
    try:
        sample_data = {'items': [{'id': 'item1', 'label': 'Test Component'}]}
        print(export_to_prov(sample_data))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)