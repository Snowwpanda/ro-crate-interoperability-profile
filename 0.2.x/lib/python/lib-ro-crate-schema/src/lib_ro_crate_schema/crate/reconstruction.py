from rdflib import Graph, RDF, RDFS, OWL, URIRef, Node
from lib_ro_crate_schema.crate.rdf import SCHEMA
from lib_ro_crate_schema.crate.type_property import TypeProperty
from typing import Dict, Any, Optional
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Node
from lib_ro_crate_schema.crate.rdf import SCHEMA
from lib_ro_crate_schema.crate.type_property import TypeProperty
from typing import Dict, Any, Optional
from pydantic import BaseModel


def resolve_reference(ref: Optional[Node], cache: Dict[URIRef, Any]) -> Optional[Any]:
    """Resolve a reference from the graph, using cache or returning a Ref wrapper."""
    match ref:
        case None:
            return None
        case URIRef() as uri if uri in cache:
            return cache[uri]
        case URIRef() as uri:
            return Ref(uri=uri)
        case _:
            raise TypeError(f"Reference must be a URIRef or None, got {type(ref)}")


class Ref(BaseModel):
    """A reference to an entity to be resolved in a second pass."""

    uri: str
    # def __init__(self, uri: URIRef) -> None:
    #     self.uri = uri
    # def __repr__(self) -> str:
    #     return f"Ref({self.uri})"


def get_subjects_by_type(graph: Graph, rdf_type: Node) -> set[Node]:
    """Return all subjects of a given rdf:type."""
    return set(graph.subjects(RDF.type, rdf_type))


def get_predicate_object_map(graph: Graph, subject: Node) -> Dict[URIRef, Node]:
    """Return a dict of predicate -> object for a given subject."""
    return {p: o for p, o in graph.predicate_objects(subject)}


def reconstruct_property(
    prop_subject: Node, props: Dict[URIRef, Node], cache: Dict[URIRef, Any]
) -> Dict[URIRef, Any]:
    # Ensure prop_subject is a URIRef
    if not isinstance(prop_subject, URIRef):
        raise TypeError(f"prop_subject must be a URIRef, got {type(prop_subject)}")
    domainIncludesRef: Optional[Node] = props.get(SCHEMA["domainIncludes"])
    domainIncludesResolved = resolve_reference(domainIncludesRef, cache)
    breakpoint()
    tp = TypeProperty(
        id=prop_subject,
        domain_includes=[domainIncludesResolved] if domainIncludesResolved else [],
    )
    cache[prop_subject] = tp
    return cache


def reconstruct_types(graph: Graph, cache: Dict[URIRef, Any]) -> Dict[URIRef, Any]:
    print("Reconstructing Classes:")
    for class_subject in get_subjects_by_type(graph, RDFS.Class):
        props = get_predicate_object_map(graph, class_subject)
        print(f"  Class: {class_subject}, {props}")
        # TODO: Instantiate Type and assign properties from cache if needed
        # cache[class_subject] = Type(...)
    return cache


def reconstruct_properties(graph: Graph, cache: Dict[URIRef, Any]) -> Dict[URIRef, Any]:
    print("Reconstructing Properties:")
    for prop_subject in get_subjects_by_type(graph, RDF.Property):
        props = get_predicate_object_map(graph, prop_subject)
        print(f"  Property: {prop_subject}, {props}")
        cache = reconstruct_property(prop_subject, props, cache)
    return cache


def reconstruct_restrictions(
    graph: Graph, cache: Dict[URIRef, Any]
) -> Dict[URIRef, Any]:
    print("Reconstructing Restrictions:")
    for restr_subject in get_subjects_by_type(graph, OWL.Restriction):
        props = get_predicate_object_map(graph, restr_subject)
        print(f"  Restriction: {restr_subject}, {props}")
        # TODO: Instantiate Restriction and add to cache
    return cache


def reconstruct_metadata_entries(
    graph: Graph, cache: Dict[URIRef, Any]
) -> Dict[URIRef, Any]:
    print("Reconstructing Metadata Entries:")
    # TODO: Implement as needed
    return cache


def reconstruct(graph: Graph) -> Dict[URIRef, Any]:
    cache: Dict[URIRef, Any] = {}
    cache = reconstruct_properties(graph, cache)
    cache = reconstruct_types(graph, cache)
    cache = reconstruct_restrictions(graph, cache)
    cache = reconstruct_metadata_entries(graph, cache)
    # TODO: Second pass to resolve Ref objects
    return cache
