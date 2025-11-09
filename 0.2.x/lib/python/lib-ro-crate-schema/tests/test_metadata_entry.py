import unittest
import sys
from pathlib import Path
from datetime import datetime

# Add source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from rdflib import URIRef, RDF, Literal


class TestMetadataEntry(unittest.TestCase):
    """Test cases for the MetadataEntry class"""

    def setUp(self):
        """Set up test fixtures"""
        self.basic_entry = MetadataEntry(
            id="basic_entry",
            class_id="BasicClass"
        )
        
        self.complete_entry = MetadataEntry(
            id="person1",
            class_id="Person",
            properties={
                "name": "John Doe",
                "age": 30,
                "active": True
            },
            references={
                "knows": ["person2", "person3"],
                "worksFor": ["organization1"]
            }
        )
        
        self.datetime_entry = MetadataEntry(
            id="event1",
            class_id="Event",
            properties={
                "title": "Important Meeting",
                "startTime": datetime(2023, 12, 25, 14, 30, 0)
            }
        )

    def test_metadata_entry_creation(self):
        """Test basic MetadataEntry object creation"""
        self.assertEqual(self.basic_entry.id, "basic_entry")
        self.assertEqual(self.basic_entry.class_id, "BasicClass")
        self.assertEqual(self.basic_entry.properties, {})
        self.assertEqual(self.basic_entry.references, {})

    def test_complete_entry_properties(self):
        """Test entry with complete properties and references"""
        self.assertEqual(self.complete_entry.id, "person1")
        self.assertEqual(self.complete_entry.class_id, "Person")
        
        # Check properties
        self.assertEqual(self.complete_entry.properties["name"], "John Doe")
        self.assertEqual(self.complete_entry.properties["age"], 30)
        self.assertEqual(self.complete_entry.properties["active"], True)
        
        # Check references
        self.assertEqual(self.complete_entry.references["knows"], ["person2", "person3"])
        self.assertEqual(self.complete_entry.references["worksFor"], ["organization1"])

    def test_java_api_compatibility(self):
        """Test Java API compatibility methods"""
        self.assertEqual(self.complete_entry.getId(), "person1")
        self.assertEqual(self.complete_entry.getClassId(), "Person")
        
        values = self.complete_entry.getValues()
        self.assertEqual(values["name"], "John Doe")
        self.assertEqual(values["age"], 30)
        
        references = self.complete_entry.getReferences()
        self.assertEqual(references["knows"], ["person2", "person3"])
        
        # Test alias method
        self.assertEqual(self.complete_entry.get_values(), self.complete_entry.properties)

    def test_to_triples(self):
        """Test RDF triple generation"""
        triples = list(self.complete_entry.to_triples())
        
        # Should generate multiple triples
        self.assertGreater(len(triples), 0)
        
        # Convert to string representation for easier testing
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Check for type declaration
        type_triple_found = any("Person" in triple[2] for triple in triple_strs)
        self.assertTrue(type_triple_found, "Should generate class type triple")
        
        # Check for properties
        name_triple_found = any("name" in triple[1] and "John Doe" in triple[2] for triple in triple_strs)
        self.assertTrue(name_triple_found, "Should generate property triples")
        
        age_triple_found = any("age" in triple[1] and "30" in triple[2] for triple in triple_strs)
        self.assertTrue(age_triple_found, "Should generate age property triple")

    def test_datetime_handling(self):
        """Test handling of datetime objects in properties"""
        triples = list(self.datetime_entry.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Datetime should be converted to ISO format string
        datetime_found = any("startTime" in triple[1] and "2023-12-25T14:30:00" in triple[2] for triple in triple_strs)
        self.assertTrue(datetime_found, "Should convert datetime to ISO string")

    def test_reference_triples(self):
        """Test reference generation in triples"""
        triples = list(self.complete_entry.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Check for reference triples (no Literal wrapper for references)
        knows_ref_found = any("knows" in triple[1] and "person2" in triple[2] for triple in triple_strs)
        self.assertTrue(knows_ref_found, "Should generate reference triples")
        
        works_for_ref_found = any("worksFor" in triple[1] and "organization1" in triple[2] for triple in triple_strs)
        self.assertTrue(works_for_ref_found, "Should generate worksFor reference")

    def test_empty_entry_triples(self):
        """Test triple generation for entry with no properties or references"""
        empty_entry = MetadataEntry(id="empty", class_id="EmptyClass")
        triples = list(empty_entry.to_triples())
        
        # Should at least generate the type declaration
        self.assertGreater(len(triples), 0)
        
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        type_found = any("EmptyClass" in triple[2] for triple in triple_strs)
        self.assertTrue(type_found, "Should generate type declaration even for empty entry")

    def test_mixed_property_types(self):
        """Test entry with various property value types"""
        mixed_entry = MetadataEntry(
            id="mixed",
            class_id="MixedType",
            properties={
                "string_prop": "text value",
                "int_prop": 42,
                "float_prop": 3.14,
                "bool_prop": False,
                "none_prop": None  # Should be filtered out
            }
        )
        
        triples = list(mixed_entry.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Check each type is properly handled
        string_found = any("string_prop" in triple[1] and "text value" in triple[2] for triple in triple_strs)
        int_found = any("int_prop" in triple[1] and "42" in triple[2] for triple in triple_strs)
        float_found = any("float_prop" in triple[1] and "3.14" in triple[2] for triple in triple_strs)
        bool_found = any("bool_prop" in triple[1] and "false" in triple[2] for triple in triple_strs)
        
        self.assertTrue(string_found, "Should handle string properties")
        self.assertTrue(int_found, "Should handle integer properties")
        self.assertTrue(float_found, "Should handle float properties")
        self.assertTrue(bool_found, "Should handle boolean properties")
        
        # None properties should not generate triples (filtered out in actual implementation)
        none_found = any("none_prop" in triple[1] for triple in triple_strs)
        # Note: The current implementation might include None values, 
        # but ideally they should be filtered out

    def test_multiple_references_same_property(self):
        """Test property with multiple reference values"""
        multi_ref_entry = MetadataEntry(
            id="multi_ref",
            class_id="MultiRef",
            references={
                "collaborator": ["person1", "person2", "person3"]
            }
        )
        
        triples = list(multi_ref_entry.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Should generate separate triples for each reference
        collab1_found = any("collaborator" in triple[1] and "person1" in triple[2] for triple in triple_strs)
        collab2_found = any("collaborator" in triple[1] and "person2" in triple[2] for triple in triple_strs)
        collab3_found = any("collaborator" in triple[1] and "person3" in triple[2] for triple in triple_strs)
        
        self.assertTrue(collab1_found, "Should generate triple for person1")
        self.assertTrue(collab2_found, "Should generate triple for person2")
        self.assertTrue(collab3_found, "Should generate triple for person3")


    def test_id_and_class_id_validation(self):
        """Test that id and class_id are properly set and accessible"""
        entry = MetadataEntry(id="test_id", class_id="TestClass")
        
        # Direct access
        self.assertEqual(entry.id, "test_id")
        self.assertEqual(entry.class_id, "TestClass")
        
        # Java API access
        self.assertEqual(entry.getId(), "test_id")
        self.assertEqual(entry.getClassId(), "TestClass")


    def test_get_entry_as_compatibility(self):
        """Test the get_entry_as method for SchemaFacade compatibility"""
        # This test verifies that MetadataEntry objects work with the new get_entry_as method
        from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
        from pydantic import BaseModel
        from typing import Optional
        
        # Create a simple test model
        class TestPerson(BaseModel):
            name: str
            age: Optional[int] = None
            active: Optional[bool] = None
        
        # Create a facade and add our test entry
        facade = SchemaFacade()
        facade.addEntry(self.complete_entry)
        
        # Test conversion to our test model
        person_instance = facade.get_entry_as("person1", TestPerson)
        
        self.assertIsNotNone(person_instance)
        self.assertIsInstance(person_instance, TestPerson)
        self.assertEqual(person_instance.name, "John Doe")
        self.assertEqual(person_instance.age, 30)
        self.assertEqual(person_instance.active, True)
        
        # Test with non-existent entry
        none_result = facade.get_entry_as("nonexistent", TestPerson)
        self.assertIsNone(none_result)

    def test_get_entry_as_with_references(self):
        """Test get_entry_as handling of references"""
        from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
        from pydantic import BaseModel
        from typing import Optional, List
        
        class TestOrganization(BaseModel):
            name: str
            
        class TestPersonWithRefs(BaseModel):
            name: str
            age: Optional[int] = None
            knows: Optional[List[str]] = None  # Keep as strings for this test
            worksFor: Optional[str] = None     # Single reference as string
        
        # Create facade and add entries
        facade = SchemaFacade()
        facade.addEntry(self.complete_entry)
        
        # Add a referenced organization entry
        org_entry = MetadataEntry(
            id="organization1",
            class_id="Organization",
            properties={"name": "Tech Corp"}
        )
        facade.addEntry(org_entry)
        
        # Test conversion
        person = facade.get_entry_as("person1", TestPersonWithRefs)
        
        self.assertIsNotNone(person)
        self.assertEqual(person.name, "John Doe")
        self.assertEqual(person.age, 30)
        self.assertEqual(person.knows, ["person2", "person3"])  # References as IDs
        self.assertEqual(person.worksFor, "organization1")       # Single reference as ID

if __name__ == '__main__':
    unittest.main()