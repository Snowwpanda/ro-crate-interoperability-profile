from pydantic import BaseModel
from .type_property import TypeProperty


class Restriction(BaseModel):
    id: str
    property_type: TypeProperty
    min_cardinality: int
    max_cardinality: int
