#!/usr/bin/env python3
"""
Minimal import example: Load external openBIS RO-Crate and print summary.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade

# Import openBIS RO-Crate from external lib/example (kept outside for now)  
crate_path = Path(__file__).parent.parent.parent.parent / "example" / "obenbis-one-publication" / "ro-crate-metadata.json"
facade = SchemaFacade.from_ro_crate(str(crate_path))

# Print summary
print(f"📁 Imported SchemaFacade with:")
print(f"   - {len(facade.types)} RDFS Classes (types)")
print(f"   - {len(facade.metadata_entries)} metadata entries")

print(f"\n📋 Types imported:")
for t in facade.types:
    props = len(t.rdfs_property or [])
    restrictions = len(t.get_restrictions())
    print(f"   - {t.id}: {props} properties, {restrictions} restrictions")

print(f"\n📦 Metadata entries:")
for entry in facade.metadata_entries[:5]:  # Show first 5
    print(f"   - {entry.id} (type: {entry.class_id})")
    
print(f"\n🎯 Ready to use! You can now:")
print(f"   - Export: facade.write('output-directory')")
print(f"   - Add data: facade.addEntry(...)")
print(f"   - Add types: facade.addType(...)")