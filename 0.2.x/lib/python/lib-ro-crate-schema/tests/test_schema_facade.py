import unittest
import sys
import json
import tempfile
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.restriction import Restriction


class TestSchemaFacade(unittest.TestCase):
    """Test cases for the SchemaFacade class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a basic schema with types and properties
        self.name_property = TypeProperty(
            id="name",
            range_includes=[LiteralType.STRING],
            required=True
        )
        
        self.age_property = TypeProperty(
            id="age",
            range_includes=[LiteralType.INTEGER],
            required=False
        )
        
        self.person_type = Type(
            id="Person",
            rdfs_property=[self.name_property, self.age_property],
            comment="A person entity",
            label="Person"
        )
        
        self.person_entry = MetadataEntry(
            id="person1",
            class_id="Person",
            properties={"name": "John Doe", "age": 30}
        )
        
        self.facade = SchemaFacade(
            types=[self.person_type],
            metadata_entries=[self.person_entry]
        )

    def test_facade_creation(self):
        """Test basic SchemaFacade creation"""
        empty_facade = SchemaFacade()
        self.assertEqual(len(empty_facade.types), 0)
        self.assertEqual(len(empty_facade.metadata_entries), 0)
        
        self.assertEqual(len(self.facade.types), 1)
        self.assertEqual(len(self.facade.metadata_entries), 1)

    def test_fluent_api(self):
        """Test fluent API methods"""
        facade = SchemaFacade()
        
        result = facade.addType(self.person_type).addEntry(self.person_entry)
        
        # Check method chaining works
        self.assertEqual(result, facade)
        
        # Check items were added
        self.assertIn(self.person_type, facade.types)
        self.assertIn(self.person_entry, facade.metadata_entries)

    def test_get_methods(self):
        """Test getter methods"""
        # Test get_types
        types = self.facade.get_types()
        self.assertEqual(len(types), 1)
        self.assertEqual(types[0].id, "Person")
        
        # Test get_type
        person_type = self.facade.get_type("Person")
        self.assertIsNotNone(person_type)
        self.assertEqual(person_type.id, "Person")
        
        non_existent = self.facade.get_type("NonExistent")
        self.assertIsNone(non_existent)
        
        # Test get_entries
        entries = self.facade.get_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].id, "person1")
        
        # Test get_entry
        person_entry = self.facade.get_entry("person1")
        self.assertIsNotNone(person_entry)
        self.assertEqual(person_entry.id, "person1")
        
        # Test get_entries_by_class
        person_entries = self.facade.get_entries_by_class("Person")
        self.assertEqual(len(person_entries), 1)
        self.assertEqual(person_entries[0].id, "person1")

    def test_java_api_compatibility(self):
        """Test Java API compatibility methods"""
        # Test property methods
        properties = self.facade.get_property_types()
        self.assertEqual(len(properties), 2)
        property_ids = [prop.id for prop in properties]
        self.assertIn("name", property_ids)
        self.assertIn("age", property_ids)
        
        # Test get_property_type
        name_prop = self.facade.get_property_type("name")
        self.assertIsNotNone(name_prop)
        self.assertEqual(name_prop.id, "name")
        
        # Test get_crate (basic functionality)
        crate = self.facade.get_crate()
        self.assertIsNotNone(crate)

    def test_to_triples(self):
        """Test RDF triple generation"""
        triples = list(self.facade.to_triples())
        
        # Should generate triples for both types and metadata entries
        self.assertGreater(len(triples), 0)
        
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Should include type definition triples
        class_triple_found = any("Class" in triple[2] for triple in triple_strs)
        self.assertTrue(class_triple_found, "Should generate class definition triples")
        
        # Should include metadata entry triples
        person_triple_found = any("person1" in triple[0] for triple in triple_strs)
        self.assertTrue(person_triple_found, "Should generate metadata entry triples")

    def test_to_graph(self):
        """Test RDF Graph generation"""
        graph = self.facade.to_graph()
        
        # Should have triples
        self.assertGreater(len(graph), 0)
        
        # Should have proper namespace binding
        namespaces = dict(graph.namespaces())
        self.assertIn('base', namespaces)

    def test_to_json(self):
        """Test JSON-LD generation"""
        json_data = self.facade.to_json()
        
        self.assertIsInstance(json_data, dict)
        self.assertIn("@context", json_data)
        self.assertIn("@graph", json_data)

    def test_write_to_crate(self):
        """Test writing to RO-Crate directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.facade.write(
                temp_dir,
                name="Test Crate",
                description="A test RO-Crate",
                license="MIT"
            )
            
            # Check that metadata file was created
            metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
            self.assertTrue(metadata_file.exists())
            
            # Check that the file contains valid JSON
            with open(metadata_file, 'r') as f:
                crate_data = json.load(f)
            
            self.assertIn("@context", crate_data)
            self.assertIn("@graph", crate_data)

    def test_from_ro_crate_roundtrip(self):
        """Test creating facade from RO-Crate and ensuring roundtrip consistency"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write original facade
            self.facade.write(temp_dir, name="Roundtrip Test")
            
            # Read back from file
            metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
            imported_facade = SchemaFacade.from_ro_crate(metadata_file)
            
            # Check that types were imported
            self.assertGreater(len(imported_facade.types), 0)
            
            # Check that metadata entries were imported
            self.assertGreater(len(imported_facade.metadata_entries), 0)

    def test_from_dict(self):
        """Test creating facade from dictionary"""
        # Create a simple RO-Crate structure
        crate_dict = {
            "@context": ["https://w3id.org/ro/crate/1.1/context"],
            "@graph": [
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": "Test Dataset"
                },
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"}
                },
                {
                    "@id": "Person",
                    "@type": "rdfs:Class",
                    "rdfs:label": "Person",
                    "rdfs:comment": "A person"
                },
                {
                    "@id": "name",
                    "@type": "rdf:Property",
                    "rdfs:label": "Name",
                    "schema:domainIncludes": {"@id": "Person"},
                    "schema:rangeIncludes": {"@id": "http://www.w3.org/2001/XMLSchema#string"}
                },
                {
                    "@id": "person1",
                    "@type": "Person",
                    "name": "Alice Johnson"
                }
            ]
        }
        
        facade = SchemaFacade.from_dict(crate_dict)
        
        # Should have imported the class
        person_type = facade.get_type("Person")
        self.assertIsNotNone(person_type)
        self.assertEqual(person_type.label, "Person")
        
        # Should have imported the metadata entry
        person_entry = facade.get_entry("person1")
        self.assertIsNotNone(person_entry)
        self.assertEqual(person_entry.class_id, "Person")

    def test_resolve_forward_refs(self):
        """Test forward reference resolution"""
        # This is mostly an internal method, but we can test it doesn't crash
        self.facade.resolve_forward_refs()
        
        # Should still have the same number of types and entries
        self.assertEqual(len(self.facade.types), 1)
        self.assertEqual(len(self.facade.metadata_entries), 1)

    def test_add_property_type(self):
        """Test adding standalone property to registry"""
        new_prop = TypeProperty(id="email", range_includes=[LiteralType.STRING])
        
        result = self.facade.add_property_type(new_prop)
        
        # Should return self for chaining
        self.assertEqual(result, self.facade)
        
        # Should be able to retrieve the property
        retrieved_prop = self.facade.get_property_type("email")
        self.assertIsNotNone(retrieved_prop)
        self.assertEqual(retrieved_prop.id, "email")

    def test_complex_schema(self):
        """Test facade with complex schema including restrictions"""
        # Create a type with custom restrictions
        title_prop = TypeProperty(id="title", range_includes=[LiteralType.STRING])
        authors_prop = TypeProperty(id="authors", range_includes=["Person"])
        
        title_restriction = Restriction(
            property_type="title",
            min_cardinality=1,
            max_cardinality=1
        )
        
        authors_restriction = Restriction(
            property_type="authors", 
            min_cardinality=1,
            max_cardinality=None  # Unbounded
        )
        
        article_type = Type(
            id="Article",
            rdfs_property=[title_prop, authors_prop],
            restrictions=[title_restriction, authors_restriction],
            comment="A research article",
            label="Article"
        )
        
        article_entry = MetadataEntry(
            id="article1",
            class_id="Article",
            properties={"title": "Great Research"},
            references={"authors": ["person1"]}
        )
        
        complex_facade = SchemaFacade(
            types=[self.person_type, article_type],
            metadata_entries=[self.person_entry, article_entry]
        )
        
        # Test that complex schema works
        self.assertEqual(len(complex_facade.types), 2)
        self.assertEqual(len(complex_facade.metadata_entries), 2)
        
        # Test restrictions are included
        article = complex_facade.get_type("Article")
        restrictions = article.get_restrictions()
        self.assertGreater(len(restrictions), 0)
        
        # Test triple generation works
        triples = list(complex_facade.to_triples())
        self.assertGreater(len(triples), 0)

    def test_empty_facade_operations(self):
        """Test operations on empty facade"""
        empty_facade = SchemaFacade()
        
        # Should handle empty operations gracefully
        self.assertEqual(len(empty_facade.get_types()), 0)
        self.assertEqual(len(empty_facade.get_entries()), 0)
        self.assertIsNone(empty_facade.get_type("NonExistent"))
        self.assertIsNone(empty_facade.get_entry("NonExistent"))
        self.assertEqual(len(empty_facade.get_entries_by_class("NonExistent")), 0)
        
        # Should still generate basic structure
        json_data = empty_facade.to_json()
        self.assertIn("@context", json_data)


if __name__ == '__main__':
    unittest.main()