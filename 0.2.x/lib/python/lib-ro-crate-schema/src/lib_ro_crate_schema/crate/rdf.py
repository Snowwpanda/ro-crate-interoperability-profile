from typing import Protocol, TypeVar, Tuple
from lib_ro_crate_schema.crate.forward_ref_resolver import ForwardRefResolver
from rdflib import Graph
from rdflib import Node, URIRef, RDF, IdentifiedNode
from rdflib import Namespace
from rdflib.namespace import NamespaceManager

Triple = Tuple[IdentifiedNode, IdentifiedNode, Node]
SCHEMA = Namespace("http://schema.org/")
BASE = Namespace("http://example.com/")


class RDFSerializable(Protocol):
    def to_rdf(self) -> list[Triple]: ...


T = TypeVar('T')

class RDFDeserializable(Protocol):
    @classmethod
    def from_rdf(cls, triples: list[Triple]): ...


class Resolvable(Protocol):
    """
    A protocol for a class that implements reference resolution
    """
    def resolve(self, reg: ForwardRefResolver): ...


def is_type(id: str, type: URIRef) -> Triple:
    """
    Prepare a triple that asserts that something
    with a certain id has `rdf:type` `type` (as a URIRef, not a Literal)
    """
    return (object_id(id), RDF.type, type)


def object_id(id: str) -> URIRef:
    return BASE[id]


def simplfy(node: Node, manager: NamespaceManager):
    if isinstance(node, URIRef):
        (base, absolute, target) = manager.compute_qname(node)
        return URIRef(f"{base}:{target}")
    else:
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
