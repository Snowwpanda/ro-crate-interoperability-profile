from typing import Literal as TLiteral
from lib_ro_crate_schema.crate.ro import RO_ID_LITERAL, RoEntity, RO_TYPE_LITERAL
from lib_ro_crate_schema.crate.ro_constants import (
    OWL_RESTRICTION,
    ON_PROPERTY,
    OWL_MAX_CARDINALITY,
    OWL_MIN_CARDINALITY,
)
from pydantic import BaseModel, Field
from rdflib import URIRef, RDF, OWL, Literal, URIRef
from lib_ro_crate_schema.crate.rdf import is_type, object_id


class OwlRestriction(BaseModel):
    id: str 
    on_property: str 
    min_cardinality: TLiteral[0, 1]
    max_cardinality: TLiteral[0, 1]

    def to_triples(self, subject=None):
        subj = object_id(self.id) if subject is None else subject
        yield is_type(self.id, URIRef(OWL_RESTRICTION))
        yield (subj, URIRef(ON_PROPERTY), URIRef(self.on_property))
        yield (subj, URIRef(OWL_MIN_CARDINALITY), Literal(self.min_cardinality))
        yield (subj, URIRef(OWL_MAX_CARDINALITY), Literal(self.max_cardinality))
