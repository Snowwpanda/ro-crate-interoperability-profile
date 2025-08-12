from typing import List, Literal
from lib_ro_crate_schema.crate.schema_facade import EQUIVALENT_CLASS, RDFS_SUBCLASS_OF
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.ro import RO_ID_LITERAL, RO_TYPE_LITERAL, RoEntity, RoReference
from pydantic import BaseModel, Field




class RdfsClass(RoEntity):
    id: str = Field(..., serialization_alias=RO_ID_LITERAL)
    self_type: str = Field("rdfs:Class", serialization_alias=RO_TYPE_LITERAL)
    subclass_of: RoReference | List[RoReference] | None = Field(..., serialization_alias=RDFS_SUBCLASS_OF) 
    ontological_annotations: List[str] | None = Field(..., serialization_alias=EQUIVALENT_CLASS)
    rdfs_properties: List[TypeProperty] | None = None



