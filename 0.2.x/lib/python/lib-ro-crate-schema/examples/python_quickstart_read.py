#!/usr/bin/env python3
"""
Python QuickStart Read Example
Mirrors the Java QuickStartRead.java for exact compatibility demonstration
"""

import sys
sys.path.append('src')

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from python_quickstart_write import write_example_crate


# Constants (matching Java pattern exactly)
TMP_EXAMPLE_CRATE = "output_crates/example-crate"

def read_example_crate():
    """
    Python QuickStart Read matching Java QuickStartRead structure exactly
    Demonstrates compatibility between Java and Python RO-Crate implementations
    """
    
    # First call write example to ensure crate exists (as requested)
    write_example_crate()
    
    # Load RO-Crate from directory (matching Java from_ro_crate pattern)
    schemaFacade = SchemaFacade.from_ro_crate(TMP_EXAMPLE_CRATE)
    
    # Display types (matching Java getTypes() approach)
    types = schemaFacade.getTypes()

    print("📚 Types in the crate:")
    for typeObj in types:
        print(f"- Type {typeObj.getId()}: {typeObj.getComment() if typeObj.getComment() else ''}")
        entries = schemaFacade.getEntries(typeObj.getId())

        for entry in entries:
            print(f"{entry.getId()} ({entry.getClassId()}): {entry.properties}")


    # Display property types
    print("📚 Properties in the crate:")
    properties = schemaFacade.getPropertyTypes()
    for prop in properties:
        print(f"{prop.getId()}: {prop.getComment() if prop.getComment() else ''} Range: {prop.getRange()}")

if __name__ == "__main__":
    read_example_crate()