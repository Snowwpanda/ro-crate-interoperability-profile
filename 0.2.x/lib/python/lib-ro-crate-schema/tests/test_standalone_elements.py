#!/usr/bin/env python3
"""
Test standalone properties and restrictions in SchemaFacade
"""

import sys
sys.path.append('src')

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.restriction import Restriction
from lib_ro_crate_schema.crate.type import Type

def test_standalone_elements():
    """Test adding and retrieving standalone properties and restrictions"""
    
    print("🧪 Testing standalone properties and restrictions...")
    
    # Create a facade
    facade = SchemaFacade()
    
    # Test 1: Add standalone property
    standalone_prop = TypeProperty(
        id="globalProperty",
        label="Global Property",
        comment="A property that exists independently of any type",
        range_includes=["xsd:string"]
    )
    
    facade.add_property_type(standalone_prop)
    print(f"✅ Added standalone property: {standalone_prop.id}")
    
    # Test 2: Add standalone restriction
    standalone_restriction = Restriction(
        id="globalRestriction",
        property_type="globalProperty",
        min_cardinality=1,
        max_cardinality=5
    )
    
    facade.add_restriction(standalone_restriction)
    print(f"✅ Added standalone restriction: {standalone_restriction.id}")
    
    # Test 3: Add a type with its own properties
    person_name_prop = TypeProperty(
        id="personName",
        label="Person Name",
        comment="Name property specific to Person type",
        range_includes=["xsd:string"]
    )
    
    person_type = Type(
        id="Person",
        label="Person",
        comment="A person entity",
        rdfs_property=[person_name_prop]
    )
    
    facade.addType(person_type)
    print(f"✅ Added type with attached property: {person_type.id}")
    
    # Test 4: Verify counts
    all_properties = facade.get_property_types()
    all_restrictions = facade.get_restrictions()
    
    print(f"\n📊 Summary:")
    print(f"   Total properties: {len(all_properties)}")
    print(f"   Total restrictions: {len(all_restrictions)}")
    print(f"   Total types: {len(facade.types)}")
    
    # Test 5: Check specific retrieval
    retrieved_prop = facade.get_property_type("globalProperty")
    retrieved_restriction = facade.get_restriction("globalRestriction")
    
    print(f"\n🔍 Specific retrieval:")
    print(f"   Retrieved global property: {'✅' if retrieved_prop else '❌'}")
    print(f"   Retrieved global restriction: {'✅' if retrieved_restriction else '❌'}")
    
    # Test 6: List all properties (standalone + type-attached)
    print(f"\n📋 All properties found:")
    for prop in all_properties:
        is_standalone = any(p.id == prop.id for p in facade.property_types)
        status = "standalone" if is_standalone else "type-attached"
        print(f"   - {prop.id} ({status})")
    
    # Test 7: Export to RDF and verify triples include standalone elements
    print(f"\n🔄 RDF export test:")
    graph = facade.to_graph()
    triple_count = len(graph)
    print(f"   Generated {triple_count} RDF triples")
    
    # Test 8: Round-trip test - export and reimport
    print(f"\n🔄 Round-trip test:")
    import os
    output_dir = "output_crates"
    os.makedirs(output_dir, exist_ok=True)
    
    test_output_path = os.path.join(output_dir, "test_standalone_output")
    facade.write(test_output_path, name="Standalone Elements Test")
    
    # Import back
    imported_facade = SchemaFacade.from_ro_crate(test_output_path)
    
    imported_properties = imported_facade.get_property_types()  
    imported_restrictions = imported_facade.get_restrictions()
    
    print(f"   Original properties: {len(all_properties)}")
    print(f"   Imported properties: {len(imported_properties)}")
    print(f"   Original restrictions: {len(all_restrictions)}")
    print(f"   Imported restrictions: {len(imported_restrictions)}")
    
    # Check if our standalone elements survived the round-trip
    survived_global_prop = imported_facade.get_property_type("globalProperty")
    survived_global_restr = imported_facade.get_restriction("globalRestriction")
    
    print(f"   Standalone property survived: {'✅' if survived_global_prop else '❌'}")
    print(f"   Standalone restriction survived: {'✅' if survived_global_restr else '❌'}")
    
    print(f"\n🎉 Test completed!")
    
    # Verify test assertions instead of returning values
    assert survived_global_prop is not None, "Standalone property should survive round-trip"
    assert survived_global_restr is not None, "Standalone restriction should survive round-trip"
    assert len(imported_properties) > 0, "Should have imported properties"
    assert len(imported_restrictions) > 0, "Should have imported restrictions"

if __name__ == "__main__":
    test_standalone_elements()
    print(f"\n📈 Test completed successfully!")