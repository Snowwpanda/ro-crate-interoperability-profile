from typing import Literal as TLiteral
from lib_ro_crate_schema.crate.owl_restriction import OwlRestriction
from lib_ro_crate_schema.crate.rdf import is_type, object_id
from lib_ro_crate_schema.crate.ro import ToRo
from lib_ro_crate_schema.crate.ro_constants import (
    OWL_MIN_CARDINALITY,
    OWL_MAX_CARDINALITY,
    OWL_RESTRICTION,
)
from pydantic import BaseModel, Field
from rdflib import URIRef, OWL, Literal, XSD
from .type_property import TypeProperty
from uuid import uuid4


class Restriction(BaseModel):
    id: str = f"{uuid4()}"
    property_type: str
    min_cardinality: TLiteral[0, 1]
    max_cardinality: TLiteral[0, 1]

    class Config:
        validate_by_name = True
        populate_by_name = True



    def to_triples(self):
        subj = object_id(self.id)
        yield is_type(self.id, OWL.Restriction)
        yield (subj, OWL.onProperty, object_id(self.property_type))
        yield (subj, OWL.minCardinality, Literal(self.min_cardinality, datatype=XSD.integer))
        yield (subj, OWL.maxCardinality, Literal(self.max_cardinality,datatype=XSD.integer))
