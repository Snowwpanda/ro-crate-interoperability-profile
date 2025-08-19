# Constants from Java SchemaFacade
from collections import defaultdict
from typing import Generator, Literal

from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.rdf import BASE, Triple, object_id
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from pydantic import BaseModel
from lib_ro_crate_schema.crate.rdf import SCHEMA
from rdflib import RDFS, RDF, Graph


type TypeRegistry = dict[TypeProperty, list[Type]]
from typing import List, Tuple

type TypeRegistry = List[Tuple[TypeProperty, Type]]


def types_to_triples(used_types: TypeRegistry) -> Generator[Triple, None, None]:
    """
    Emits all the triples
    that represent the types found in the TypeRegistry
    Each key is a TypeProperty, each value is a list of Type objects using it.
    """
    for property_obj, cls in used_types:
        prop_with_domain = property_obj.model_copy(
            update=dict(domain_includes=[cls.id])
        )
        yield from prop_with_domain.to_triples()


class SchemaFacade(BaseModel):
    types: list[Type]
    metadata_entries: list[MetadataEntry]
    prefix: str = "base"

    def to_triples(self) -> Generator[Triple, None, None]:
        for p in self.types:
            yield from p.to_triples()
        for m in self.metadata_entries:
            yield from m.to_triples()

    def get_properties(self) -> Generator[TypeProperty, None, None]:
        yield from set(
            [
                property
                for current_type in self.types
                for property in current_type.rdfs_property
            ]
        )

    def to_graph(self) -> Graph:
        local_graph = Graph()
        [local_graph.add(triple) for triple in self.to_triples()]
        local_graph.bind(prefix=self.prefix, namespace=BASE)
        return local_graph
