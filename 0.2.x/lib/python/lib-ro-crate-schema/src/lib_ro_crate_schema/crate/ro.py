from lib_ro_crate_schema.crate.schema_facade import RDFS_CLASS, OWL_RESTRICTION
from pydantic import BaseModel, Field
from typing import Literal, Protocol, TypeVar, Generic

RO_TYPE_LITERAL = "@type"
RO_ID_LITERAL = "@id"

ALLOWED_RO_SCHEMA_TYPES = Literal["rdfs:Class"] | Literal["owl:Restriction"] | Literal["rdfs:Property"]

# class RoId(BaseModel):
#     """
#     This class is a wapper to represent the @id propery 
#     in JSON-LS
#     """
#     id: str = Field(..., serialization_alias=RO_ID_LITERAL)

class RoReference(BaseModel):
    """
    This class encodes the reference to another object through its @id
    """
    id: str = Field(..., serialization_alias=RO_ID_LITERAL)


class RoEntity(BaseModel):
    """
    This is the base class to represent a RO-Crate graph entity
    which as minimum members should offer id and its own type as
    @id and @type
    """
    id: str = Field(..., serialization_alias=RO_ID_LITERAL)
    self_type: str = Field(..., serialization_alias=RO_TYPE_LITERAL)


T = TypeVar("T")

class ToRo(Protocol[T]):
    """
    This is a protocol (a static duck typed class)
    that allows for each class to define what behavior it should implement.
    In this way we can for example say that `Type` should implement ToRo[RdfsClass]
    """
    def to_ro(self) -> T:
        ...