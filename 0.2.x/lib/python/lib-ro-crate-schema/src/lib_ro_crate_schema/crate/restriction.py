from typing import Literal
from lib_ro_crate_schema.crate.owl_restriction import OwlRestriction
from lib_ro_crate_schema.crate.ro import ToRo
from lib_ro_crate_schema.crate.ro_constants import (
    OWL_MIN_CARDINALITY,
    OWL_MAX_CARDINALITY,
    OWL_RESTRICTION,
)
from pydantic import BaseModel, Field
from .type_property import TypeProperty


class Restriction(BaseModel):
    id: str
    property_type: str
    min_cardinality: Literal[0, 1]
    max_cardinality: Literal[0, 1]

    class Config:
        validate_by_name = True
        populate_by_name = True

    def to_ro(self):
        return OwlRestriction(
            id=self.id,
            self_type=OWL_RESTRICTION,
            on_property=self.property_type,
            min_cardinality=self.min_cardinality,
            max_cardinality=self.max_cardinality,
        )

    def to_triples(self, subject=None):
        yield from self.to_ro().to_triples(subject=subject)
