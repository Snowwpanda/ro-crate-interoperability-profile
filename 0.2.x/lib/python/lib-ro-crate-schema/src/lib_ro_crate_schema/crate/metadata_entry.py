from pydantic import BaseModel

class MetadataEntry(BaseModel):
    id: str
    types: set[str] | None = None
    props: dict[str, str] | None = None
    references : dict[str, list[str]] | None = None 
    children_identifiers: list[str] | None = None
    parent_identifiers: list[str] | None = None
   

 