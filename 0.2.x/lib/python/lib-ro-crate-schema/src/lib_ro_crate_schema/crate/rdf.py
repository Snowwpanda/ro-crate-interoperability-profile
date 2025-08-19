from typing import Protocol
from rdflib import Graph
from rdflib import Node, URIRef, RDF, IdentifiedNode
from rdflib import Namespace
from rdflib.namespace import NamespaceManager
from typing import TypeVar

type Triple = tuple[IdentifiedNode, IdentifiedNode, Node]
SCHEMA = Namespace("http://schema.org/")
BASE = Namespace("http://example.com/")


class RDFSerializable(Protocol):
    def to_rdf(self) -> list[Triple]: ...


class RDFDeserializable[T](Protocol):
    @classmethod
    def from_rdf(cls, triples: list[Triple]): ...


def is_type(id: str, type: URIRef) -> Triple:
    """
    Prepare a triple that asserts that something
    with a certain id has `rdf:type` `type` (as a URIRef, not a Literal)
    """
    return (object_id(id), RDF.type, type)


def object_id(id: str) -> URIRef:
    return BASE[id]


def simplfy(node: Node, manager: NamespaceManager):
    match node:
        case URIRef(ref):
            (base, absolute, target) = manager.compute_qname(ref)
            return URIRef(f"{base}:{target}")
        case _:
            return node


def unbind(g: Graph) -> Graph:
    nm = g.namespace_manager
    new_graph = Graph()
    for s, p, o in g:
        s_new = simplfy(s, nm)
        p_new = simplfy(p, nm)
        o_new = simplfy(o, nm)
        new_graph.add((s_new, p_new, o_new))
    return new_graph
