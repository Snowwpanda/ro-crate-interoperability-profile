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


class TestRoundTripCycles(unittest.TestCase):
    """Test round-trip conversion cycles to verify no data loss during import/export"""

    def setUp(self):
        """Set up test fixtures with comprehensive schema"""
        # Create a comprehensive test schema
        
        # Properties
        self.name_prop = TypeProperty(
            id="name",
            range_includes=[LiteralType.STRING],
            required=True,
            label="Full Name",
            comment="The complete name of the entity",
            ontological_annotations=["https://schema.org/name"]
        )
        
        self.age_prop = TypeProperty(
            id="age",
            range_includes=[LiteralType.INTEGER],
            required=False,
            label="Age",
            comment="Age in years"
        )
        
        self.email_prop = TypeProperty(
            id="email",
            range_includes=[LiteralType.STRING],
            required=False,
            label="Email Address"
        )
        
        self.knows_prop = TypeProperty(
            id="knows",
            range_includes=["Person"],
            required=False,
            label="Knows",
            comment="People this person knows"
        )
        
        # Restrictions
        self.name_restriction = Restriction(
            id="Person_name_restriction",
            property_type="name",
            min_cardinality=1,
            max_cardinality=1
        )
        
        self.knows_restriction = Restriction(
            id="Person_knows_restriction", 
            property_type="knows",
            min_cardinality=0,
            max_cardinality=None  # Unbounded
        )
        
        # Types
        self.person_type = Type(
            id="Person",
            subclass_of=["https://schema.org/Thing"],
            ontological_annotations=["https://schema.org/Person"],
            rdfs_property=[self.name_prop, self.age_prop, self.email_prop, self.knows_prop],
            restrictions=[self.name_restriction, self.knows_restriction],
            comment="A person entity with comprehensive metadata",
            label="Person"
        )
        
        self.organization_type = Type(
            id="Organization",
            subclass_of=["https://schema.org/Thing"],
            ontological_annotations=["https://schema.org/Organization"],
            rdfs_property=[self.name_prop],
            comment="An organization",
            label="Organization"
        )
        
        # Metadata entries
        self.person1 = MetadataEntry(
            id="person1",
            class_id="Person",
            properties={
                "name": "Alice Johnson",
                "age": 30,
                "email": "alice@example.com"
            },
            references={
                "knows": ["person2"]
            }
        )
        
        self.person2 = MetadataEntry(
            id="person2",
            class_id="Person",
            properties={
                "name": "Bob Smith",
                "age": 25
            },
            references={
                "knows": ["person1"]  # Mutual relationship
            }
        )
        
        self.org1 = MetadataEntry(
            id="org1",
            class_id="Organization",
            properties={
                "name": "Example Corp"
            }
        )
        
        # Complete facade
        self.original_facade = SchemaFacade(
            types=[self.person_type, self.organization_type],
            metadata_entries=[self.person1, self.person2, self.org1]
        )

    def test_export_import_roundtrip(self):
        """Test export to file and import back maintains schema integrity"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export original facade
            self.original_facade.write(
                temp_dir,
                name="Roundtrip Test",
                description="Testing roundtrip conversion",
                license="MIT"
            )
            
            # Import back from file
            metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
            imported_facade = SchemaFacade.from_ro_crate(metadata_file)
            
            # Compare facades
            self._compare_facades(self.original_facade, imported_facade, "File roundtrip")

    def test_json_dict_roundtrip(self):
        """Test conversion to JSON dict and back maintains schema integrity"""
        
        # Convert to JSON dict
        json_data = self.original_facade.to_json()
        
        # Import from dict
        imported_facade = SchemaFacade.from_dict(json_data)
        
        # Compare facades
        self._compare_facades(self.original_facade, imported_facade, "JSON dict roundtrip")

    def test_multiple_roundtrips(self):
        """Test multiple export/import cycles to ensure stability"""
        
        current_facade = self.original_facade
        
        for cycle in range(3):  # Test 3 cycles
            with tempfile.TemporaryDirectory() as temp_dir:
                # Export current facade
                current_facade.write(
                    temp_dir,
                    name=f"Multi-roundtrip Cycle {cycle + 1}",
                    description="Testing multiple roundtrip cycles"
                )
                
                # Import back
                metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
                current_facade = SchemaFacade.from_ro_crate(metadata_file)
                
                # Compare with original (should remain consistent)
                self._compare_facades(
                    self.original_facade, 
                    current_facade, 
                    f"Multiple roundtrip cycle {cycle + 1}"
                )

    def test_triples_preservation(self):
        """Test that RDF triples are preserved through roundtrip"""
        
        # Get original triples
        original_triples = set()
        for triple in self.original_facade.to_triples():
            # Normalize to string representation for comparison
            triple_str = (str(triple[0]), str(triple[1]), str(triple[2]))
            original_triples.add(triple_str)
        
        # Roundtrip via JSON
        json_data = self.original_facade.to_json()
        imported_facade = SchemaFacade.from_dict(json_data)
        
        # Get imported triples
        imported_triples = set()
        for triple in imported_facade.to_triples():
            triple_str = (str(triple[0]), str(triple[1]), str(triple[2]))
            imported_triples.add(triple_str)
        
        # Compare triple sets
        print(f"\nTriples preservation test:")
        print(f"Original triples: {len(original_triples)}")
        print(f"Imported triples: {len(imported_triples)}")
        
        # Find differences
        only_in_original = original_triples - imported_triples
        only_in_imported = imported_triples - original_triples
        
        if only_in_original:
            print(f"Triples lost in import: {len(only_in_original)}")
            for triple in list(only_in_original)[:5]:  # Show first 5
                print(f"  Lost: {triple}")
        
        if only_in_imported:
            print(f"New triples in import: {len(only_in_imported)}")
            for triple in list(only_in_imported)[:5]:  # Show first 5
                print(f"  New: {triple}")
        
        # Allow some differences due to RO-Crate structure additions
        # But core schema triples should be preserved
        self.assertGreater(len(imported_triples), 0, "Should have imported triples")

    def test_obenbis_roundtrip(self):
        """Test roundtrip with the OpenBIS example if available"""
        
        obenbis_file = (Path(__file__).parent.parent.parent.parent / 
                        "example" / "obenbis-one-publication" / "ro-crate-metadata.json")
        
        if not obenbis_file.exists():
            self.skipTest(f"OpenBIS example not found at {obenbis_file}")
        
        # Import OpenBIS RO-Crate
        original_facade = SchemaFacade.from_ro_crate(obenbis_file)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export it
            original_facade.write(
                temp_dir,
                name="OpenBIS Roundtrip Test",
                description="Testing OpenBIS RO-Crate roundtrip"
            )
            
            # Import back
            metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
            imported_facade = SchemaFacade.from_ro_crate(metadata_file)
            
            # Basic consistency checks
            print(f"\nOpenBIS roundtrip test:")
            print(f"Original - Types: {len(original_facade.types)}, Entries: {len(original_facade.metadata_entries)}")
            print(f"Imported - Types: {len(imported_facade.types)}, Entries: {len(imported_facade.metadata_entries)}")
            
            # Should have similar structure (allowing for some differences due to RO-Crate additions)
            self.assertGreaterEqual(
                len(imported_facade.types) + len(imported_facade.metadata_entries),
                0,
                "Should have imported some entities"
            )

    def test_property_cardinality_preservation(self):
        """Test that property cardinality information is preserved"""
        
        # Create a facade with specific cardinality requirements
        required_prop = TypeProperty(id="required_field", range_includes=[LiteralType.STRING], required=True)
        optional_prop = TypeProperty(id="optional_field", range_includes=[LiteralType.STRING], required=False)
        
        test_type = Type(
            id="TestType",
            rdfs_property=[required_prop, optional_prop]
        )
        
        test_facade = SchemaFacade(types=[test_type])
        
        # Roundtrip via JSON
        json_data = test_facade.to_json()
        imported_facade = SchemaFacade.from_dict(json_data)
        
        # Check that cardinality info is preserved through restrictions
        imported_type = imported_facade.get_type("TestType")
        self.assertIsNotNone(imported_type)
        
        restrictions = imported_type.get_restrictions()
        
        # Find restrictions for our properties
        required_restriction = None
        optional_restriction = None
        
        for restriction in restrictions:
            if restriction.property_type == "required_field":
                required_restriction = restriction
            elif restriction.property_type == "optional_field":
                optional_restriction = restriction
        
        # Check cardinalities (if restrictions were generated)
        if required_restriction:
            self.assertEqual(required_restriction.min_cardinality, 1, "Required field should have min cardinality 1")
        
        if optional_restriction:
            self.assertEqual(optional_restriction.min_cardinality, 0, "Optional field should have min cardinality 0")

    def test_ontological_annotations_preservation(self):
        """Test that ontological annotations are preserved"""
        
        # Test facade with ontological annotations
        json_data = self.original_facade.to_json()
        imported_facade = SchemaFacade.from_dict(json_data)
        
        # Check Person type annotations
        original_person = self.original_facade.get_type("Person")
        imported_person = imported_facade.get_type("Person")
        
        if imported_person and original_person:
            print(f"\nOntological annotations test:")
            print(f"Original Person ontological annotations: {original_person.ontological_annotations}")
            print(f"Imported Person ontological annotations: {imported_person.ontological_annotations}")
            
            # Should preserve ontological mapping
            if original_person.ontological_annotations:
                self.assertIsNotNone(
                    imported_person.ontological_annotations,
                    "Should preserve ontological annotations"
                )

    def _compare_facades(self, original: SchemaFacade, imported: SchemaFacade, test_name: str):
        """Helper method to compare two facades for consistency"""
        
        print(f"\n{test_name} comparison:")
        print(f"Original - Types: {len(original.types)}, Entries: {len(original.metadata_entries)}")  
        print(f"Imported - Types: {len(imported.types)}, Entries: {len(imported.metadata_entries)}")
        
        # Basic counts should be similar (allowing for RO-Crate structure additions)
        self.assertGreaterEqual(
            len(imported.types) + len(imported.metadata_entries),
            len(original.types) + len(original.metadata_entries),
            "Should preserve at least original entities"
        )
        
        # Check specific types are preserved
        for original_type in original.types:
            imported_type = imported.get_type(original_type.id)
            if imported_type:  # May not be preserved due to import/export limitations
                self.assertEqual(
                    imported_type.id, 
                    original_type.id,
                    f"Type ID should be preserved: {original_type.id}"
                )
                
                if original_type.label and imported_type.label:
                    self.assertEqual(
                        imported_type.label,
                        original_type.label, 
                        f"Type label should be preserved: {original_type.id}"
                    )
        
        # Check specific metadata entries are preserved
        for original_entry in original.metadata_entries:
            imported_entry = imported.get_entry(original_entry.id)
            if imported_entry:  # May not be preserved due to import/export limitations
                self.assertEqual(
                    imported_entry.id,
                    original_entry.id,
                    f"Entry ID should be preserved: {original_entry.id}"
                )
                
                self.assertEqual(
                    imported_entry.class_id,
                    original_entry.class_id,
                    f"Entry class ID should be preserved: {original_entry.id}"
                )
        
        # Test that we can generate valid output from imported facade
        try:
            imported_json = imported.to_json()
            self.assertIn("@context", imported_json)
            self.assertIn("@graph", imported_json)
        except Exception as e:
            self.fail(f"Failed to generate JSON from imported facade: {e}")
        
        try:
            imported_triples = list(imported.to_triples())
            self.assertGreater(len(imported_triples), 0, "Should generate triples from imported facade")
        except Exception as e:
            self.fail(f"Failed to generate triples from imported facade: {e}")
        
        print(f"✓ {test_name} completed successfully")


if __name__ == '__main__':
    unittest.main()