from lib_ro_crate_schema.crate.ro import RO_ID_LITERAL
from pydantic import BaseModel, Field

class MetadataEntry(BaseModel):
    id: str =  Field(..., serialization_alias=RO_ID_LITERAL)
    types: set[str] | None = Field(..., alias="@types")
    props: dict[str, str] | None = None
    references : dict[str, list[str]] | None = None 
    children_identifiers: list[str] | None = None
    parent_identifiers: list[str] | None = None
   

 