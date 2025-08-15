# Constants from Java SchemaFacade
from typing import Literal

from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.type import Type
from pydantic import BaseModel




class SchemaFacade(BaseModel):
    types: list[Type]
    metadata_entries: list[MetadataEntry]
