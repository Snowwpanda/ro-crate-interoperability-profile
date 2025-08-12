from typing import Literal
from lib_ro_crate_schema.crate.ro import RO_ID_LITERAL, RoEntity, RO_TYPE_LITERAL
from lib_ro_crate_schema.crate.schema_facade import OWL_RESTRICTION, ON_PROPERTY, OWL_MAX_CARDINALITY, OWL_MIN_CARDINALITY
from pydantic import BaseModel, Field



class OwlRestriction(RoEntity):
    id: str =  Field(..., serialization_alias=RO_ID_LITERAL)
    self_type: str = Field(..., serialization_alias=RO_TYPE_LITERAL)
    on_property: str =  Field(..., serialization_alias=ON_PROPERTY)
    min_cardinality: Literal[0, 1] = Field(...,serialization_alias= OWL_MIN_CARDINALITY)
    max_cardinality: Literal[0, 1] = Field(...,serialization_alias= OWL_MAX_CARDINALITY)