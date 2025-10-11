#!/usr/bin/env python3

"""
Test the refactored get_crate method to ensure it works independently.
"""

import sys
sys.path.append('src')

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.restriction import Restriction

def test_get_crate_method():
    print("🧪 Testing get_crate method...")
    
    # Create a simple schema
    facade = SchemaFacade()
    
    # Add a simple type with a property
    name_prop = TypeProperty(
        id="name",
        range_includes=["http://www.w3.org/2001/XMLSchema#string"],
        required=True
    )
    
    person_type = Type(
        id="Person",
        rdfs_property=[name_prop],
        comment="A person entity"
    )
    
    facade.addType(person_type)
    
    # Add a metadata entry
    person_entry = MetadataEntry(
        id="john_doe",
        class_id="Person", 
        properties={"name": "John Doe"}
    )
    
    facade.addEntry(person_entry)
    
    # Test get_crate method
    print("📦 Testing get_crate method...")
    crate = facade.get_crate(
        name="Test RO-Crate",
        description="A test crate created using get_crate method"
    )
    
    print(f"✅ Created crate: {crate}")
    print(f"✅ Crate name: {getattr(crate, 'name', 'Not set')}")
    print(f"✅ Crate description: {getattr(crate, 'description', 'Not set')}")
    
    # Test that the crate can be written
    print("💾 Testing crate writing...")
    import os
    output_dir = "output_crates"
    os.makedirs(output_dir, exist_ok=True)
    
    test_get_crate_path = os.path.join(output_dir, "test_get_crate_output")
    crate.write(test_get_crate_path)
    print(f"✅ Crate written successfully to '{test_get_crate_path}'")
    
    # Test that write method still works (using get_crate internally)
    print("💾 Testing write method (should use get_crate internally)...")
    test_write_path = os.path.join(output_dir, "test_write_output")
    facade.write(test_write_path, name="Test via Write", description="Using write method")
    print("✅ Write method works correctly")
    
    print("🎉 All tests passed!")

if __name__ == "__main__":
    test_get_crate_method()