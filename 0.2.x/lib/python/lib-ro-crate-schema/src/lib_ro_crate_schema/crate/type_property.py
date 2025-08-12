from typing import List, Optional, Union

from lib_ro_crate_schema.crate.schema_facade import RDFS_PROPERTY, DOMAIN_IDENTIFIER
from .literal_type import LiteralType
from pydantic import BaseModel, Field
from rocrate.model import Person
from rocrate.model.contextentity import ContextEntity
from .ro import RO_ID_LITERAL, RO_TYPE_LITERAL, RoEntity, RoReference, RoReferences, serialize_references

class TypeProperty(BaseModel):
    id: str = Field(..., serialization_alias=RO_TYPE_LITERAL)
    label: Optional[str] = None
    comment: Optional[str] = None
    domain_includes: Optional[List[str]] = None
    range_includes: Optional[List[str]] = None
    range_includes_data_type: Optional[List[LiteralType]] = None
    ontological_annotations: Optional[List[str]] = None

    def to_ro(self):
        RoTypeProperty(
            id = self.id,
            self_type=RDFS_PROPERTY,
            label = self.label,
            comment=self.comment,
            domain_includes=RoDomain(domain_includes=serialize_references(self.domain_includes))
        )

class RoDomain(BaseModel):
    domain_includes: RoReferences = Field(..., serialization_alias=DOMAIN_IDENTIFIER)

class RoTypeProperty(RoEntity):
    id: str = Field(..., serialization_alias=RO_ID_LITERAL)
    self_type: str = Field(RDFS_PROPERTY, serialization_alias=RO_TYPE_LITERAL)
    label: Optional[str] = None
    comment: Optional[str] = None
    domain_includes: Optional[List[str]] = None
    range_includes: Optional[List[str]] = None
    range_includes_data_type: Optional[List[LiteralType]] = None
    ontological_annotations: Optional[List[str]] = None

