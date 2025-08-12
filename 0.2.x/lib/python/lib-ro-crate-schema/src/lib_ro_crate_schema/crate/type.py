from typing import List, Optional, Union

from lib_ro_crate_schema.crate.rdfs_class import RdfsClass
from .literal_type import LiteralType
from .restriction import Restriction
from .type_property import TypeProperty, RoTypeProperty
from .ro import RoReference, ToRo, serialize_references
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

    def to_ro(self) -> RdfsClass:
        return RdfsClass(id=self.id, 
                  self_type="rdfs:Class", 
                  subclass_of=serialize_references(self.subclass_of),
                  rdfs_properties=[prop for popr in self.rdfs_property] if self.rdfs_property is not None,
                  ontological_annotations=None, rdfs_properties=None),

        


    # def to_ro(self):
    #     return RdfsClass(
    #         id=RoId(id=self.id),
    #         subclass_of=[RoId(id=i) for i in self.subclass_of if i] if self.subclass_of else [],
    #         ontological_annotations=
    #         equivalent_class=
    #     )
