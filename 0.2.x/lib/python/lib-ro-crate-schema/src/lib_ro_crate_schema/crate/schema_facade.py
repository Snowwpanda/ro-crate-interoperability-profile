# Constants from Java SchemaFacade
from collections import defaultdict
from typing import Generator, Literal

from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.rdf import Triple, object_id
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from pydantic import BaseModel
from lib_ro_crate_schema.crate.rdf import SCHEMA
from rdflib import RDFS, RDF


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
        prop_with_domain = property_obj.model_copy(update=dict(domain_includes=[cls.id]))
        yield from prop_with_domain.to_triples()
    


class SchemaFacade(BaseModel):
    types: list[Type]
    properties: list[TypeProperty]
    metadata_entries: list[MetadataEntry]

    def collect_properties(self) -> TypeRegistry:
        """
        Creates a registry of RDFS properties used in all RDFS classes.
        Maps TypeProperty objects to the list of Type objects using them.
        """
        result: List[Tuple[TypeProperty, Type]] = []
        for cls in self.types:
            for prop in getattr(cls, 'rdfs_property', []):
                result.append((prop, cls))
        return result



    def to_triples(self) -> Generator[Triple, None, None]:
        registry = self.collect_properties()

        yield from types_to_triples(registry)
        for p in self.types:
            yield from p.to_triples()
        for m in self.metadata_entries:
            yield from m.to_triples()