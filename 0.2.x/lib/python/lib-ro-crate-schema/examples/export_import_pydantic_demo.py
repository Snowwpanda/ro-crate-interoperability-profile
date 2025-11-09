#!/usr/bin/env python3
"""
Demonstration of exporting Pydantic models from SchemaFacade.

This example shows how to:
1. Create a schema with Type definitions
2. Export those Types as Pydantic model classes
3. Use the generated classes to create and validate instances
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.restriction import Restriction
from lib_ro_crate_schema.crate.literal_type import LiteralType
from pydantic import BaseModel
from typing import List, Optional


def main():
    print("🔧 RO-Crate Pydantic Export Demo")
    print("=" * 50)
    
    # Create SchemaFacade and add some types
    # For this demo, we'll define two types: Person and Organization
    # The ro-crate-schema will not be exported as crate, just used here for model generation
    facade = SchemaFacade()
    
    # Define Person type, starting with the properties and restrictions
    person_name_prop = TypeProperty(
        id="name",
        label="Full Name", 
        comment="The complete name of the person",
        range_includes=["http://www.w3.org/2001/XMLSchema#string"],
        required=True
    )
    
    person_age_prop = TypeProperty(
        id="age",
        label="Age",
        comment="Age in years",
        range_includes=["http://www.w3.org/2001/XMLSchema#integer"],
        required=False
    )
    
    person_emails_prop = TypeProperty(
        id="emails",
        label="Email Addresses",
        comment="List of email addresses",
        range_includes=["http://www.w3.org/2001/XMLSchema#string"],
        required=False
    )
    
    # Create restrictions
    person_name_restriction = Restriction(
        property_type="name",
        min_cardinality=1,
        max_cardinality=1
    )
    
    person_age_restriction = Restriction(
        property_type="age", 
        min_cardinality=0,
        max_cardinality=1
    )
    
    person_emails_restriction = Restriction(
        property_type="emails",
        min_cardinality=0,
        max_cardinality=None  # Unbounded list
    )
    
    person_type = Type(
        id="Person",
        label="Person",
        comment="Represents a person with personal information",
        subclass_of=["https://schema.org/Person"],
        rdfs_property=[person_name_prop, person_age_prop, person_emails_prop],
        restrictions=[person_name_restriction, person_age_restriction, person_emails_restriction]
    )
    
    # Define Organization type, starting with properties and restrictions
    org_name_prop = TypeProperty(
        id="name",
        label="Organization Name",
        comment="The official name of the organization",
        range_includes=["http://www.w3.org/2001/XMLSchema#string"],
        required=True
    )
    
    org_employees_prop = TypeProperty(
        id="employees", 
        label="Employees",
        comment="People working for this organization",
        range_includes=["Person"],  # Reference to Person type
        required=False
    )
    
    org_name_restriction = Restriction(
        property_type="name",
        min_cardinality=1,
        max_cardinality=1
    )
    
    org_employees_restriction = Restriction(
        property_type="employees",
        min_cardinality=0,
        max_cardinality=None  # Unbounded list
    )
    
    organization_type = Type(
        id="Organization",
        label="Organization", 
        comment="Represents an organization or company",
        subclass_of=["https://schema.org/Organization"],
        rdfs_property=[org_name_prop, org_employees_prop],
        restrictions=[org_name_restriction, org_employees_restriction]
    )
    
    # Add types to facade
    facade.addType(person_type)
    facade.addType(organization_type)
    
    print("📋 Schema created with types:")
    for type_def in facade.get_types():
        print(f"  - {type_def.id}: {type_def.comment}")
    
    print("\n🏗️  Exporting Pydantic models...")
    
    # Export individual model
    print("\n1️⃣ Export single model:")
    PersonModel = facade.export_pydantic_model("Person")
    print(f"Generated class: {PersonModel.__name__}")
    print(f"Fields: {list(PersonModel.__annotations__.keys())}")
    
    # Export all models
    print("\n2️⃣ Export all models:")
    models = facade.export_all_pydantic_models()
    print("Generated models:")
    for name, model_class in models.items():
        print(f"  - {name}: {model_class.__name__}")
        print(f"    Fields: {list(model_class.__annotations__.keys())}")
    
    print("\n✨ Testing generated models...")
    
    # Test Person model
    print("\n👤 Creating Person instances:")
    try:
        # Valid person with required field
        person1 = PersonModel(name="Alice Johnson", age=30, emails=["alice@example.com", "alice.j@work.com"])
        print(f"✅ Created person: {person1.name}, age {person1.age}")
        print(f"   Emails: {person1.emails}")
        
        # Person with only required fields
        person2 = PersonModel(name="Bob Smith")
        print(f"✅ Created person: {person2.name} (minimal)")
        
        # Test validation - missing required field
        print("\n🔍 Testing validation:")
        try:
            invalid_person = PersonModel(age=25)  # Missing required 'name'
            print("❌ This should have failed!")
        except Exception as e:
            print(f"✅ Validation caught error: {e}")
            
    except Exception as e:
        print(f"❌ Error creating person: {e}")
    
    # Test Organization model
    print("\n🏢 Creating Organization instances:")
    try:
        OrganizationModel = models["Organization"]
        
        # Note: For now, forward references to other models need to be handled carefully
        # In a real implementation, you'd want to resolve these properly
        person_as_dict = {"name": "Charlie Brown", "age": 28}
        org = OrganizationModel(name="Acme Corporation", employees=[person1, person_as_dict])
        print(f"✅ Created organization: {org.name} with employees {[emp.name for emp in org.employees]}")

        # Test validation - employees must be person instances or dicts with the right fields
        try:
            invalid_org = OrganizationModel(name="Invalid Org", employees=["Not a person"])
            print("❌ This should have failed!")
        except Exception as e:
            print(f"✅ Validation caught error: {e}")


        
        # Test validation - employees missing name (required field) will fail
        fake_person = {"firstname": "Fake", "lastname": "Person"}
        try:
            invalid_org = OrganizationModel(name="Invalid Org", employees=[fake_person])
            print("❌ This should have failed!")
        except Exception as e:
            print(f"✅ Validation caught error: {e}")
        
    except Exception as e:
        print(f"❌ Error creating organization: {e}")
    
    print("\n🎯 Model schemas:")
    print("\nPerson model schema:")
    try:
        print(PersonModel.model_json_schema())
    except Exception as e:
        print(f"Schema generation error: {e}")
    
    print("\n🎉 Pydantic export demo completed!")
    print("\n💡 Key features demonstrated:")
    print("  ✓ Export Type definitions as Pydantic model classes")
    print("  ✓ Handle required vs optional fields from OWL restrictions")
    print("  ✓ Support list fields (unbounded cardinality)")
    print("  ✓ Map RDF types to Python types")
    print("  ✓ Generate proper Pydantic validation")
    print("  ✓ Preserve field metadata (descriptions)")


if __name__ == "__main__":
    main()