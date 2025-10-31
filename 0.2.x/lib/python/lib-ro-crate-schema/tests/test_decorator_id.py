#!/usr/bin/env python3
"""
Test the enhanced @ro_crate_schema decorator with explicit id parameter.
"""

import sys
sys.path.append('src')

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.decorators import ro_crate_schema, Field
from pydantic import BaseModel

# Test the new 'id' parameter in the decorator
@ro_crate_schema(
    id="CustomPerson", 
    ontology="https://schema.org/Person"
)
class PersonModel(BaseModel):
    """A person model with explicit ID different from class name"""
    name: str = Field(ontology="https://schema.org/name")
    email: str = Field(ontology="https://schema.org/email")

# Test without explicit ID (should default to class name)
@ro_crate_schema(ontology="https://schema.org/Dataset")  
class DatasetModel(BaseModel):
    """A dataset model without explicit ID"""
    title: str = Field(ontology="https://schema.org/name")
    description: str = Field(ontology="https://schema.org/description")

def test_decorator_with_id():
    print("🧪 Testing @ro_crate_schema decorator with explicit id parameter...")
    
    # Create facade and add models
    facade = SchemaFacade()
    facade.add_all_registered_models()
    
    print("\n📊 Registered types:")
    for type_obj in facade.get_types():
        print(f"  - Type ID: '{type_obj.id}' (from class: {type_obj.__class__.__name__})")
        
    # Verify that PersonModel got the custom ID "CustomPerson"
    person_type = facade.get_type("CustomPerson")
    dataset_type = facade.get_type("DatasetModel")  # Should use class name
    
    if person_type:
        print(f"✅ Found PersonModel with custom ID: '{person_type.id}'")
    else:
        print("❌ PersonModel with custom ID not found")
        
    if dataset_type:
        print(f"✅ Found DatasetModel with default ID: '{dataset_type.id}'")
    else:
        print("❌ DatasetModel with default ID not found")
    
    # Create instances and add them
    person = PersonModel(name="Alice Johnson", email="alice@example.com")
    dataset = DatasetModel(title="Test Dataset", description="A test dataset")
    
    facade.add_model_instance(person, "alice")
    facade.add_model_instance(dataset, "test_dataset")
    
    print("\n📦 Metadata entries:")
    for entry in facade.get_entries():
        print(f"  - {entry.id} (class_id: {entry.class_id})")
        
    # Verify the entries use the correct type IDs
    alice_entry = facade.get_entry("alice")
    dataset_entry = facade.get_entry("test_dataset")
    
    if alice_entry and alice_entry.class_id == "CustomPerson":
        print("✅ Alice entry correctly references 'CustomPerson' type")
    else:
        print(f"❌ Alice entry has wrong class_id: {alice_entry.class_id if alice_entry else 'None'}")
        
    if dataset_entry and dataset_entry.class_id == "DatasetModel":
        print("✅ Dataset entry correctly references 'DatasetModel' type")
    else:
        print(f"❌ Dataset entry has wrong class_id: {dataset_entry.class_id if dataset_entry else 'None'}")
    
    # Export and verify
    print("\n💾 Testing RO-Crate export...")
    import os
    output_dir = "output_crates"
    os.makedirs(output_dir, exist_ok=True)
    
    test_output_path = os.path.join(output_dir, "test_decorator_id_output")
    facade.write(test_output_path, name="Test ID Parameter")
    print("✅ Export successful!")
    
    print("\n🎉 Test completed successfully!")

if __name__ == "__main__":
    test_decorator_with_id()