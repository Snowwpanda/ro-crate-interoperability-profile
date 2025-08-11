from typing import List
from lib_ro_crate_schema.crate.type_property import TypeProperty
from pydantic import BaseModel


class RdfsClass(BaseModel):
    id: str
    type: str
    subclass_of: List[str] | None = None 
    ontological_annotations: List[str] | None = None
    rdfs_properties: List[TypeProperty] | None = None



