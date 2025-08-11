from typing import List, Optional, Union
from .literal_type import LiteralType
from .restriction import Restriction
from .type_property import TypeProperty
from pydantic import BaseModel


class Type(BaseModel):
    id: str
    type: str
    subclass_of: List[str] | None
    ontological_annotations: List[str] | None
    rdfs_property: List[TypeProperty] | None
    comment: str
    label: str
    restrictions: List[Restriction] | None
