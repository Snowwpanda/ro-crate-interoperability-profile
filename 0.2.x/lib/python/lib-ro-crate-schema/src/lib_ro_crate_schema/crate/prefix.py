from rdflib import Graph, URIRef
from rdflib.namespace import split_uri


def split_namespace(node: URIRef) -> tuple[str, str]:
    try:
        namespace, local = split_uri(node)
    except ValueError:
        namespace, local = "", str(node)
    return namespace, local


def extract_uses_namespaces(gr: Graph) -> list[tuple[str, str]]:
    ns = set()
    for n in gr.all_nodes():
        match n:
            case URIRef(uri):
                ns.add(split_namespace(uri)[0])
    return ns
