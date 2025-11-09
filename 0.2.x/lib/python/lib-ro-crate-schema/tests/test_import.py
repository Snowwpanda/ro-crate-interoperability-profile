#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.decorators import ro_crate_schema, Field

@ro_crate_schema(ontology="http://openbis.org/Equipment")
class Equipment(BaseModel):
    """Laboratory equipment with optional nesting"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    model: str = Field(json_schema_extra={"comment": "Equipment model/version"})
    serial_number: str = Field(json_schema_extra={"ontology": "https://schema.org/serialNumber"})
    created_date: datetime = Field(json_schema_extra={"ontology": "https://schema.org/dateCreated"})
    parent_equipment: Optional['Equipment'] = Field(default=None, json_schema_extra={"ontology": "https://schema.org/isPartOf"})

def test_export():
    facade = SchemaFacade()
    
    # Create parent equipment
    parent = Equipment(
        name="Parent Equipment",
        model="P1",
        serial_number="P001",
        created_date=datetime(2023, 1, 1),
        parent_equipment=None
    )
    
    # Create child equipment with parent reference
    child = Equipment(
        name="Child Equipment", 
        model="C1",
        serial_number="C001",
        created_date=datetime(2023, 2, 1),
        parent_equipment=parent
    )
    
    # Add to facade
    facade.add_model_instance(parent, "base:parent")
    facade.add_model_instance(child, "base:child") 
    
    # Export
    import os
    output_dir = "output_crates"
    os.makedirs(output_dir, exist_ok=True)
    test_output_path = os.path.join(output_dir, "test_simple")
    
    facade.write(test_output_path, "Simple Test", "Testing reference export")
    print(f"Export completed - check {test_output_path}/ro-crate-metadata.json")

if __name__ == "__main__":
    test_export()