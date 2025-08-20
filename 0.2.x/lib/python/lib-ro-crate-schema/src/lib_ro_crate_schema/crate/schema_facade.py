# Constants from Java SchemaFacade
from collections import defaultdict
from typing import Generator, Literal

from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.rdf import BASE, Triple, object_id
from lib_ro_crate_schema.crate.registry import Registry
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.restriction import Restriction
from pydantic import BaseModel, Field, PrivateAttr
from lib_ro_crate_schema.crate.rdf import SCHEMA
from rdflib import RDFS, RDF, Graph

from lib_ro_crate_schema.crate.registry import ForwardRef
from typing import Any
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
    """
    `_registry` stores a registry of properties and types
    to allow forward references to other types
    """

    _registry: Registry[Type | TypeProperty | Restriction] = PrivateAttr(
        default=Registry()
    )
    types: list[Type]
    metadata_entries: list[MetadataEntry]
    prefix: str = "base"

    def model_post_init(self, context: Any) -> None:
        """
        Register all classes and properties for later reference resolution.
        Convert all string refs in properties to ForwardRef using Pydantic post-init.
        """
        for current_type in self.types:
            self._registry.register(current_type.id, current_type)
            if current_type.rdfs_property:
                for prop in current_type.rdfs_property:
                    self._registry.register(prop.id, prop)
        super().model_post_init(context)

    def resolve_ref[T](self, ref: str | ForwardRef[T]) -> T:
        """
        Resolve a reference (ForwardRef, str, or id) to the actual object using the registry.
        """
        match ref:
            case ForwardRef(ref=ref_id):
                return self._registry.resolve(ref_id)
            case str(ref_id):
                return self._registry.resolve(ref_id)
            case _:
                return ref

    def resolve_forward_refs(self):
        """
        Walk all types/properties and delegate reference resolution to each property.
        """
        for current_type in self.types:
            current_type.resolve(self._registry)
        # for current_type in self.types:
        #     if current_type.rdfs_property:
        #         for prop in current_type.rdfs_property:
        #             if hasattr(prop, "resolve_references"):
        #                 prop.resolve_references(self)

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
