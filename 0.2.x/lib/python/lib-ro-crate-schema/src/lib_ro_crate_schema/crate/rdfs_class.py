from typing import List, Literal
from lib_ro_crate_schema.crate.ro_constants import RDFS_SUBCLASS_OF
from lib_ro_crate_schema.crate.type_property import TypeProperty, RoTypeProperty
from lib_ro_crate_schema.crate.ro import (
    EQUIVALENT_CLASS,
    RO_ID_LITERAL,
    RO_TYPE_LITERAL,
    RoEntity,
    RoReference,
)
from pydantic import BaseModel, Field
from rdflib import URIRef, RDF, RDFS, Literal, Node
from lib_ro_crate_schema.crate.rdf import is_type


class RdfsClass(RoEntity):
    id: str = Field(..., serialization_alias=RO_ID_LITERAL)
    self_type: str = Field("rdfs:Class", serialization_alias=RO_TYPE_LITERAL)
    subclass_of: RoReference | List[RoReference] | List[str] = Field(
        ..., serialization_alias=RDFS_SUBCLASS_OF
    )
    ontological_annotations: List[str] | None = Field(
        ..., serialization_alias=EQUIVALENT_CLASS
    )
    rdfs_properties: List[RoTypeProperty] | None = None

    def to_triples(self, subject=None):
        subj = URIRef(self.id) if subject is None else subject
        yield is_type(self.id, RDFS.Class)
        if self.subclass_of:
            parents = self.subclass_of if isinstance(self.subclass_of, list) else [self.subclass_of]
            for parent in parents:
                yield (subj, RDFS.subClassOf, URIRef(str(parent)))
        if self.ontological_annotations:
            for eq in self.ontological_annotations:
                yield (subj, URIRef(EQUIVALENT_CLASS), URIRef(str(eq)))
        if self.rdfs_properties:
            for prop in self.rdfs_properties:
                yield from prop.to_triples(subject=subj)
