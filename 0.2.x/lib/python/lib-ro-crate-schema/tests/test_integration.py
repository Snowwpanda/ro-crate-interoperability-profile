import unittest
import sys
import json
import tempfile
from pathlib import Path

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry


class TestIntegrationExamples(unittest.TestCase):
    """Integration tests using real examples from the codebase"""

    def setUp(self):
        """Set up paths to example files"""
        self.test_dir = Path(__file__).parent
        self.examples_dir = self.test_dir.parent.parent / "examples"
        self.lib_dir = self.test_dir.parent
        self.obenbis_crate = self.lib_dir.parent.parent / "example" / "obenbis-one-publication" / "ro-crate-metadata.json"

    def test_examples_py_recreation(self):
        """Test recreating the example from examples.py"""
        
        # Recreate the example schema from examples.py
        name = TypeProperty(
            id="name", 
            range_includes=[LiteralType.STRING],
            required=True,
            label="Full Name",
            comment="The full name of the entity"
        )
        
        identifier = TypeProperty(
            id="identifier", 
            range_includes=[LiteralType.STRING],
            required=True,
            label="Identifier", 
            comment="Unique identifier for the entity"
        )

        colleague = TypeProperty(
            id="colleague", 
            range_includes=["Participant"],
            required=False,
            label="Colleague",
            comment="Optional colleague relationship"
        )

        participant_type = Type(
            id="Participant",
            subclass_of=["https://schema.org/Thing"],
            ontological_annotations=["http://purl.org/dc/terms/creator"],
            rdfs_property=[name, identifier],
            comment="A participant in the research",
            label="Participant",
        )

        creator_type = Type(
            id="Creator",
            subclass_of=["https://schema.org/Thing"],
            ontological_annotations=["http://purl.org/dc/terms/creator"],
            rdfs_property=[name, identifier, colleague],
            comment="A creator of the research work",
            label="Creator",
        )

        creator_entry = MetadataEntry(
            id="creator1",
            class_id="Creator",
            properties={
                "name": "John Author",
                "identifier": "https://orcid.org/0000-0000-0000-0000",
            },
            references={},
        )

        participant_entry = MetadataEntry(
            id="participant",
            class_id="Participant", 
            properties={
                "name": "Karl Participant",
                "identifier": "https://orcid.org/0000-0000-0000-0001",
            },
            references={
                "colleague": ["creator1"]
            },
        )

        schema = SchemaFacade(
            types=[creator_type, participant_type],
            metadata_entries=[creator_entry, participant_entry],
        )
        
        # Test the schema
        self.assertEqual(len(schema.types), 2)
        self.assertEqual(len(schema.metadata_entries), 2)
        
        # Test types
        creator = schema.get_type("Creator")
        self.assertIsNotNone(creator)
        self.assertEqual(creator.label, "Creator")
        self.assertEqual(len(creator.rdfs_property), 3)  # name, identifier, colleague
        
        participant = schema.get_type("Participant")
        self.assertIsNotNone(participant)
        self.assertEqual(participant.label, "Participant")
        self.assertEqual(len(participant.rdfs_property), 2)  # name, identifier
        
        # Test metadata entries
        creator_md = schema.get_entry("creator1")
        self.assertIsNotNone(creator_md)
        self.assertEqual(creator_md.properties["name"], "John Author")
        
        participant_md = schema.get_entry("participant")
        self.assertIsNotNone(participant_md)
        self.assertEqual(participant_md.references["colleague"], ["creator1"])
        
        # Test triple generation
        triples = list(schema.to_triples())
        self.assertGreater(len(triples), 0)
        
        # Test JSON generation
        json_data = schema.to_json()
        self.assertIn("@context", json_data)
        self.assertIn("@graph", json_data)

    def test_obenbis_import(self):
        """Test importing the OpenBIS one-publication RO-Crate"""
        
        if not self.obenbis_crate.exists():
            self.skipTest(f"OpenBIS example file not found at {self.obenbis_crate}")
        
        # Import the OpenBIS RO-Crate
        facade = SchemaFacade.from_ro_crate(self.obenbis_crate)
        
        # Test that import was successful
        self.assertIsNotNone(facade)
        
        # Should have imported some types and/or metadata entries
        total_items = len(facade.types) + len(facade.metadata_entries)
        self.assertGreater(total_items, 0, "Should have imported some schema elements")
        
        # Test that we can generate JSON-LD from imported data
        json_data = facade.to_json()
        self.assertIn("@context", json_data)
        self.assertIn("@graph", json_data)
        
        # Test that we can generate triples
        triples = list(facade.to_triples())
        self.assertGreater(len(triples), 0, "Should generate RDF triples")
        
        print(f"Imported facade with {len(facade.types)} types and {len(facade.metadata_entries)} metadata entries")
        
        # If we have types, test they have proper structure
        if facade.types:
            first_type = facade.types[0]
            self.assertIsNotNone(first_type.id)
            print(f"First imported type: {first_type.id}")
        
        # If we have metadata entries, test they have proper structure  
        if facade.metadata_entries:
            first_entry = facade.metadata_entries[0]
            self.assertIsNotNone(first_entry.id)
            self.assertIsNotNone(first_entry.class_id)
            print(f"First imported entry: {first_entry.id} of type {first_entry.class_id}")

    def test_obenbis_structure_analysis(self):
        """Test analyzing the structure of the OpenBIS RO-Crate"""
        
        if not self.obenbis_crate.exists():
            self.skipTest(f"OpenBIS example file not found at {self.obenbis_crate}")
        
        # Read raw JSON to analyze structure
        with open(self.obenbis_crate, 'r') as f:
            crate_data = json.load(f)
        
        self.assertIn("@graph", crate_data)
        graph = crate_data["@graph"]
        
        # Analyze what types of entities are in the crate
        entity_types = {}
        rdfs_classes = []
        rdf_properties = []
        owl_restrictions = []
        metadata_entities = []
        
        for item in graph:
            item_type = item.get("@type", "Unknown")
            item_id = item.get("@id", "")
            
            if item_type == "rdfs:Class":
                rdfs_classes.append(item_id)
            elif item_type in ["rdf:Property", "rdfs:Property"]:
                rdf_properties.append(item_id)
            elif item_type == "owl:Restriction":
                owl_restrictions.append(item_id)
            elif item_id not in ["./", "ro-crate-metadata.json"]:
                metadata_entities.append((item_id, item_type))
            
            # Count entity types
            if item_type in entity_types:
                entity_types[item_type] += 1
            else:
                entity_types[item_type] = 1
        
        print("\nOpenBIS RO-Crate structure analysis:")
        print(f"Total entities: {len(graph)}")
        print(f"RDFS Classes: {len(rdfs_classes)}")
        print(f"RDF Properties: {len(rdf_properties)}")
        print(f"OWL Restrictions: {len(owl_restrictions)}")
        print(f"Metadata entities: {len(metadata_entities)}")
        
        print("\nEntity type distribution:")
        for entity_type, count in sorted(entity_types.items()):
            print(f"  {entity_type}: {count}")
        
        # Test that the structure makes sense
        self.assertGreater(len(graph), 0, "Should have entities in the graph")
        
        if rdfs_classes:
            print(f"\nSample RDFS Classes: {rdfs_classes[:5]}")
        if rdf_properties:
            print(f"Sample RDF Properties: {rdf_properties[:5]}")
        if metadata_entities:
            print(f"Sample Metadata Entities: {[f'{id} ({type})' for id, type in metadata_entities[:5]]}")

    def test_create_minimal_example(self):
        """Test creating a minimal working example similar to examples.py"""
        
        # Create a minimal Person schema
        name_prop = TypeProperty(
            id="name",
            range_includes=[LiteralType.STRING],
            required=True,
            label="Name"
        )
        
        email_prop = TypeProperty(
            id="email",
            range_includes=[LiteralType.STRING],
            required=False,
            label="Email"
        )
        
        person_type = Type(
            id="Person",
            rdfs_property=[name_prop, email_prop],
            label="Person",
            comment="A person entity"
        )
        
        # Create a person instance
        person_instance = MetadataEntry(
            id="john_doe",
            class_id="Person",
            properties={
                "name": "John Doe",
                "email": "john@example.com"
            }
        )
        
        # Create facade
        facade = SchemaFacade(
            types=[person_type],
            metadata_entries=[person_instance]
        )
        
        # Test basic functionality
        self.assertEqual(len(facade.types), 1)
        self.assertEqual(len(facade.metadata_entries), 1)
        
        # Test export to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            facade.write(
                temp_dir,
                name="Minimal Example",
                description="A minimal RO-Crate example",
                license="CC0"
            )
            
            # Verify files were created
            metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
            self.assertTrue(metadata_file.exists())
            
            # Verify the JSON structure
            with open(metadata_file, 'r') as f:
                exported_data = json.load(f)
            
            self.assertIn("@context", exported_data)
            self.assertIn("@graph", exported_data)
            
            # Check that our Person type and instance are included
            graph = exported_data["@graph"]
            
            person_class_found = any(
                (item.get("@id") in ["Person", "base:Person", "http://example.com/Person"]) and item.get("@type") == "rdfs:Class"
                for item in graph
            )
            self.assertTrue(person_class_found, "Should export Person class")
            
            person_instance_found = any(
                (item.get("@id") in ["john_doe", "base:john_doe", "http://example.com/john_doe"]) and 
                item.get("@type") in ["Person", "base:Person", "http://example.com/Person"]
                for item in graph
            )
            self.assertTrue(person_instance_found, "Should export person instance")
            
            print(f"\nMinimal example exported with {len(graph)} entities")

    def test_complex_relationship_example(self):
        """Test creating example with complex relationships between entities"""
        
        # Define properties
        name_prop = TypeProperty(id="name", range_includes=[LiteralType.STRING], required=True)
        title_prop = TypeProperty(id="title", range_includes=[LiteralType.STRING], required=True)
        author_prop = TypeProperty(id="author", range_includes=["Person"], required=True)
        publisher_prop = TypeProperty(id="publisher", range_includes=["Organization"], required=False)
        
        # Define types
        person_type = Type(
            id="Person",
            rdfs_property=[name_prop],
            label="Person"
        )
        
        organization_type = Type(
            id="Organization", 
            rdfs_property=[name_prop],
            label="Organization"
        )
        
        article_type = Type(
            id="Article",
            rdfs_property=[title_prop, author_prop, publisher_prop],
            label="Article"
        )
        
        # Create instances
        author = MetadataEntry(
            id="author1",
            class_id="Person",
            properties={"name": "Dr. Jane Smith"}
        )
        
        publisher = MetadataEntry(
            id="pub1",
            class_id="Organization",
            properties={"name": "Academic Press"}
        )
        
        article = MetadataEntry(
            id="article1",
            class_id="Article",
            properties={"title": "Advanced RO-Crate Techniques"},
            references={
                "author": ["author1"],
                "publisher": ["pub1"]
            }
        )
        
        # Create facade
        facade = SchemaFacade(
            types=[person_type, organization_type, article_type],
            metadata_entries=[author, publisher, article]
        )
        
        # Test relationships
        self.assertEqual(len(facade.types), 3)
        self.assertEqual(len(facade.metadata_entries), 3)
        
        # Test that references work correctly
        article_entry = facade.get_entry("article1")
        self.assertIn("author1", article_entry.references["author"])
        self.assertIn("pub1", article_entry.references["publisher"])
        
        # Test triple generation includes relationships
        triples = list(facade.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Should have triples linking article to author and publisher
        author_ref_found = any(
            "article1" in triple[0] and "author" in triple[1] and "author1" in triple[2]
            for triple in triple_strs
        )
        self.assertTrue(author_ref_found, "Should generate author reference triple")
        
        publisher_ref_found = any(
            "article1" in triple[0] and "publisher" in triple[1] and "pub1" in triple[2] 
            for triple in triple_strs
        )
        self.assertTrue(publisher_ref_found, "Should generate publisher reference triple")
        
        print(f"\nComplex relationship example generated {len(triples)} triples")


if __name__ == '__main__':
    unittest.main()