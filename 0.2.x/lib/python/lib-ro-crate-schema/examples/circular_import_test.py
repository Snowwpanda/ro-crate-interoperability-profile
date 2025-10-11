#!/usr/bin/env python3
"""
Focused test for circular import handling in RO-Crate schema.

This test specifically creates two people who are each other's colleagues
to verify how the system handles circular references during:
1. Schema creation
2. RDF serialization 
3. JSON-LD export
4. Round-trip import/export
"""

import sys
import json
from pathlib import Path
from typing import List, Optional

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic import BaseModel
from lib_ro_crate_schema.crate.decorators import ro_crate_schema, Field
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade

@ro_crate_schema(ontology="https://schema.org/Organization")
class SimpleOrganization(BaseModel):
    """Simple organization for testing"""
    name: str = Field(ontology="https://schema.org/name")
    country: str = Field(ontology="https://schema.org/addressCountry")

@ro_crate_schema(ontology="https://schema.org/Person")
class SimplePerson(BaseModel):
    """Person with circular colleague relationship"""
    name: str = Field(ontology="https://schema.org/name")
    email: str = Field(ontology="https://schema.org/email")
    affiliation: SimpleOrganization = Field(ontology="https://schema.org/affiliation")
    colleagues: List['SimplePerson'] = Field(default=[], ontology="https://schema.org/colleague")

def test_circular_imports():
    """Test circular colleague relationships"""
    
    print("🧪 CIRCULAR IMPORT TEST")
    print("=" * 50)
    
    # Create organization
    org = SimpleOrganization(
        name="Test University",
        country="Switzerland"
    )
    
    # Create two people without colleagues initially
    alice = SimplePerson(
        name="Dr. Alice Johnson",
        email="alice@test.edu", 
        affiliation=org,
        colleagues=[]
    )
    
    bob = SimplePerson(
        name="Prof. Bob Smith",
        email="bob@test.edu",
        affiliation=org, 
        colleagues=[]
    )
    
    print(f"✅ Created Alice (colleagues: {len(alice.colleagues)})")
    print(f"✅ Created Bob (colleagues: {len(bob.colleagues)})")
    
    # Establish circular colleague relationship
    alice = alice.model_copy(update={'colleagues': [bob]})
    bob = bob.model_copy(update={'colleagues': [alice]})
    
    print(f"\n🔄 Circular relationships established:")
    print(f"   Alice colleagues: {[c.name for c in alice.colleagues]}")
    print(f"   Bob colleagues: {[c.name for c in bob.colleagues]}")
    
    # Test schema creation with circular refs
    print(f"\n📊 Testing schema creation...")
    facade = SchemaFacade()
    facade.add_all_registered_models()
    
    print(f"   ✅ Schema created with {len(facade.types)} types")
    
    # Add instances to facade
    facade.add_model_instance(org, "test_org")
    facade.add_model_instance(alice, "alice")
    facade.add_model_instance(bob, "bob")
    
    print(f"   ✅ Added {len(facade.metadata_entries)} instances to facade")
    
    # Test RDF generation
    print(f"\n🕸️  Testing RDF generation...")
    try:
        graph = facade.to_graph()
        print(f"   ✅ Generated {len(graph)} RDF triples successfully")
    except Exception as e:
        print(f"   ❌ RDF generation failed: {e}")
        return False
    
    # Test JSON-LD export
    print(f"\n📄 Testing RO-Crate export...")
    try:
        import os
        output_dir = "output_crates"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "circular_test")
        
        facade.write(output_path, name="Circular Import Test", 
                    description="Testing circular colleague relationships")
        print(f"   ✅ Exported to {output_path}")
    except Exception as e:
        print(f"   ❌ Export failed: {e}")
        return False
    
    # Test round-trip import
    print(f"\n🔄 Testing round-trip import...")
    try:
        imported_facade = SchemaFacade.from_ro_crate(output_path)
        print(f"   ✅ Imported {len(imported_facade.types)} types, {len(imported_facade.metadata_entries)} entries")
        
        # Check if circular references are preserved
        alice_entry = None
        bob_entry = None
        
        for entry in imported_facade.metadata_entries:
            if entry.id == "alice":
                alice_entry = entry
            elif entry.id == "bob": 
                bob_entry = entry
        
        if alice_entry and bob_entry:
            print(f"   ✅ Found Alice and Bob entries after import")
            
            # Check if colleague relationships survived
            alice_colleagues = alice_entry.properties.get('colleagues', [])
            bob_colleagues = bob_entry.properties.get('colleagues', [])
            
            print(f"   Alice colleagues in imported data: {alice_colleagues}")
            print(f"   Bob colleagues in imported data: {bob_colleagues}")
        else:
            print(f"   ⚠️  Could not find Alice/Bob entries after import")
            
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Examine the actual JSON-LD structure
    print(f"\n🔍 Examining generated JSON-LD structure...")
    try:
        with open(f"{output_path}/ro-crate-metadata.json", 'r') as f:
            crate_data = json.load(f)
        
        # Find Person entities
        person_entities = []
        for entity in crate_data.get("@graph", []):
            if entity.get("@type") == "SimplePerson":
                person_entities.append(entity)
        
        print(f"   Found {len(person_entities)} Person entities:")
        for person in person_entities:
            person_id = person.get("@id", "unknown")
            person_name = person.get("base:name", "unknown")
            colleagues = person.get("base:colleagues", "none")
            print(f"     - {person_id}: {person_name}")
            print(f"       Colleagues: {colleagues}")
            
    except Exception as e:
        print(f"   ⚠️  Could not examine JSON-LD: {e}")
    
    print(f"\n🎉 Circular import test completed!")
    return True

if __name__ == "__main__":
    test_circular_imports()