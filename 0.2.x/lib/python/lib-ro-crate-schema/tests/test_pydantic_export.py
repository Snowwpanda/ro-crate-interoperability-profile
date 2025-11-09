"""
Test suite for Pydantic model export functionality in SchemaFacade.
"""

import unittest
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.restriction import Restriction
from pydantic import BaseModel, ValidationError


class TestPydanticExport(unittest.TestCase):
    """Test Pydantic model export functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.facade = SchemaFacade()
        
        # Create a simple Person type
        person_name_prop = TypeProperty(
            id="name",
            label="Name",
            comment="Person's name",
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
        
        person_type = Type(
            id="Person",
            label="Person",
            comment="A person",
            rdfs_property=[person_name_prop, person_age_prop],
            restrictions=[
                Restriction(property_type="name", min_cardinality=1, max_cardinality=1),
                Restriction(property_type="age", min_cardinality=0, max_cardinality=1)
            ]
        )
        
        self.facade.addType(person_type)
    
    def test_export_single_model(self):
        """Test exporting a single model"""
        PersonModel = self.facade.export_pydantic_model("Person")
        
        # Check class properties
        self.assertEqual(PersonModel.__name__, "Person")
        self.assertIn("name", PersonModel.__annotations__)
        self.assertIn("age", PersonModel.__annotations__)
        
        # Test instance creation
        person = PersonModel(name="Alice")
        self.assertEqual(person.name, "Alice")
        self.assertIsNone(person.age)
        
        # Test validation
        with self.assertRaises(ValidationError):
            PersonModel()  # Missing required 'name'
    
    def test_export_all_models(self):
        """Test exporting all models"""
        models = self.facade.export_all_pydantic_models()
        
        self.assertIn("Person", models)
        PersonModel = models["Person"]
        
        # Test functionality
        person = PersonModel(name="Bob", age=30)
        self.assertEqual(person.name, "Bob")
        self.assertEqual(person.age, 30)
    
    def test_type_mapping(self):
        """Test RDF type to Python type mapping"""
        # Test different data types
        string_type = self.facade._rdf_type_to_python_type(["http://www.w3.org/2001/XMLSchema#string"])
        self.assertEqual(string_type, str)
        
        int_type = self.facade._rdf_type_to_python_type(["http://www.w3.org/2001/XMLSchema#integer"])
        self.assertEqual(int_type, int)
        
        bool_type = self.facade._rdf_type_to_python_type(["http://www.w3.org/2001/XMLSchema#boolean"])
        self.assertEqual(bool_type, bool)
        
        # Test schema.org types
        schema_text = self.facade._rdf_type_to_python_type(["https://schema.org/Text"])
        self.assertEqual(schema_text, str)
    
    def test_field_requirements(self):
        """Test field requirement detection from restrictions"""
        person_type = self.facade.get_type("Person")
        
        # name should be required (minCardinality: 1)
        self.assertTrue(self.facade._is_field_required(person_type, "name"))
        
        # age should be optional (minCardinality: 0)
        self.assertFalse(self.facade._is_field_required(person_type, "age"))
    
    def test_list_fields(self):
        """Test list field detection"""
        # Add a type with list property
        list_prop = TypeProperty(
            id="tags",
            label="Tags",
            range_includes=["http://www.w3.org/2001/XMLSchema#string"]
        )
        
        list_type = Type(
            id="TaggedItem",
            rdfs_property=[list_prop],
            restrictions=[
                Restriction(property_type="tags", min_cardinality=0, max_cardinality=None)  # Unbounded
            ]
        )
        
        self.facade.addType(list_type)
        
        # Test list detection
        self.assertTrue(self.facade._is_field_list(list_type, "tags"))
        
        # Export and test
        TaggedModel = self.facade.export_pydantic_model("TaggedItem")
        tagged = TaggedModel(tags=["tag1", "tag2"])
        self.assertEqual(tagged.tags, ["tag1", "tag2"])
    
    def test_forward_references(self):
        """Test forward references between models"""
        # Add Organization type that references Person
        org_name_prop = TypeProperty(
            id="name",
            label="Organization Name", 
            range_includes=["http://www.w3.org/2001/XMLSchema#string"]
        )
        
        org_members_prop = TypeProperty(
            id="members",
            label="Members",
            range_includes=["Person"]  # Forward reference
        )
        
        org_type = Type(
            id="Organization",
            rdfs_property=[org_name_prop, org_members_prop],
            restrictions=[
                Restriction(property_type="name", min_cardinality=1, max_cardinality=1),
                Restriction(property_type="members", min_cardinality=0, max_cardinality=None)
            ]
        )
        
        self.facade.addType(org_type)
        
        # Export all models (should handle forward references)
        models = self.facade.export_all_pydantic_models()
        
        # Test that both models were created
        self.assertIn("Person", models)
        self.assertIn("Organization", models)
        
        # Test basic functionality (forward ref might not work perfectly but shouldn't crash)
        OrgModel = models["Organization"]
        org = OrgModel(name="Test Corp")
        self.assertEqual(org.name, "Test Corp")
    
    def test_nonexistent_type(self):
        """Test error handling for nonexistent types"""
        with self.assertRaises(ValueError):
            self.facade.export_pydantic_model("NonExistentType")
    
    def test_custom_base_class(self):
        """Test using custom base class"""
        class CustomBase(BaseModel):
            custom_field: str = "default"
        
        PersonModel = self.facade.export_pydantic_model("Person", base_class=CustomBase)
        
        # Should inherit from custom base
        self.assertTrue(issubclass(PersonModel, CustomBase))
        
        # Should have both custom and schema fields
        person = PersonModel(name="Test")
        self.assertEqual(person.name, "Test")
        self.assertEqual(person.custom_field, "default")
    
    def test_field_metadata(self):
        """Test that field metadata is preserved"""
        PersonModel = self.facade.export_pydantic_model("Person")
        
        # Check model schema includes field descriptions
        schema = PersonModel.model_json_schema()
        self.assertIn("Person's name", schema["properties"]["name"]["description"])
        self.assertIn("Age in years", schema["properties"]["age"]["description"])


if __name__ == "__main__":
    unittest.main()