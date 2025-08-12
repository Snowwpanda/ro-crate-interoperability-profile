from typing import List, Optional, Union

from lib_ro_crate_schema.crate.rdfs_class import RdfsClass
from .literal_type import LiteralType
from .restriction import Restriction
from .type_property import TypeProperty
from .ro import RoReference, ToRo
from pydantic import BaseModel


def serialize_subclass_of(value: List[str] | str | None):
    match value:
        case None:
            return None
        case str(val) | [val]:
            return RoReference(id=val)
        case [vals] as ls:
            return [RoReference(id=sc) for sc in ls]

class Type(BaseModel):
    id: str 
    type: str
    subclass_of: List[str] | None
    ontological_annotations: List[str] | None
    rdfs_property: List[TypeProperty] | None
    comment: str
    label: str
    restrictions: List[Restriction] | None

    def to_ro(self) -> RdfsClass:
        return RdfsClass(id=self.id, 
                  self_type="rdfs:Class", 
                  subclass_of=serialize_subclass_of(self.subclass_of),
                  ontological_annotations=None, rdfs_properties=None)
        


    # def to_ro(self):
    #     return RdfsClass(
    #         id=RoId(id=self.id),
    #         subclass_of=[RoId(id=i) for i in self.subclass_of if i] if self.subclass_of else [],
    #         ontological_annotations=
    #         equivalent_class=
    #     )
