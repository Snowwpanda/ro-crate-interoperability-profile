from typing import List, Optional, Union
from .literal_type import LiteralType
from pydantic import BaseModel


class TypeProperty(BaseModel):
    id: str
    label: Optional[str] = None
    comment: Optional[str] = None
    domain_includes: Optional[List[str]] = None
    range_includes: Optional[List[str]] = None
    range_includes_data_type: Optional[List[LiteralType]] = None
    ontological_annotations: Optional[List[str]] = None
