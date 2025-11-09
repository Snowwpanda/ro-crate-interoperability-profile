import unittest
import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.restriction import Restriction
from rdflib import OWL, Literal, XSD


class TestRestriction(unittest.TestCase):
    """Test cases for the Restriction class"""

    def setUp(self):
        """Set up test fixtures"""
        self.basic_restriction = Restriction(property_type="testProperty")
        
        self.complete_restriction = Restriction(
            id="complete_restriction",
            property_type="name",
            min_cardinality=1,
            max_cardinality=1
        )
        
        self.unbounded_restriction = Restriction(
            property_type="tags",
            min_cardinality=0,
            max_cardinality=None  # Unbounded
        )

    def test_restriction_creation(self):
        """Test basic Restriction object creation"""
        self.assertEqual(self.basic_restriction.property_type, "testProperty")
        self.assertIsNone(self.basic_restriction.min_cardinality)
        self.assertIsNone(self.basic_restriction.max_cardinality)
        self.assertIsNotNone(self.basic_restriction.id)  # Auto-generated UUID

    def test_restriction_with_cardinalities(self):
        """Test restriction with explicit cardinalities"""
        self.assertEqual(self.complete_restriction.property_type, "name")
        self.assertEqual(self.complete_restriction.min_cardinality, 1)
        self.assertEqual(self.complete_restriction.max_cardinality, 1)

    def test_unbounded_restriction(self):
        """Test restriction with unbounded max cardinality"""
        self.assertEqual(self.unbounded_restriction.property_type, "tags")
        self.assertEqual(self.unbounded_restriction.min_cardinality, 0)
        self.assertIsNone(self.unbounded_restriction.max_cardinality)

    def test_to_triples(self):
        """Test RDF triple generation"""
        triples = list(self.complete_restriction.to_triples())
        
        # Should generate multiple triples
        self.assertGreater(len(triples), 0)
        
        # Convert to string representation for easier testing
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Check for essential triples
        type_triple_found = any("Restriction" in triple[2] for triple in triple_strs)
        self.assertTrue(type_triple_found, "Should generate owl:Restriction type triple")
        
        on_property_found = any("onProperty" in triple[1] for triple in triple_strs)
        self.assertTrue(on_property_found, "Should generate owl:onProperty triple")
        
        min_card_found = any("minCardinality" in triple[1] for triple in triple_strs)
        self.assertTrue(min_card_found, "Should generate owl:minCardinality triple")
        
        max_card_found = any("maxCardinality" in triple[1] for triple in triple_strs)
        self.assertTrue(max_card_found, "Should generate owl:maxCardinality triple")

    def test_minimal_restriction_triples(self):
        """Test triple generation for restriction with no cardinalities"""
        minimal = Restriction(property_type="minimal_prop")
        triples = list(minimal.to_triples())
        
        # Should at least generate type and onProperty triples
        self.assertGreater(len(triples), 0)
        
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        type_found = any("Restriction" in triple[2] for triple in triple_strs)
        self.assertTrue(type_found, "Should generate owl:Restriction type")
        
        on_property_found = any("onProperty" in triple[1] for triple in triple_strs)
        self.assertTrue(on_property_found, "Should generate owl:onProperty")
        
        # Should NOT generate cardinality triples when they're None
        min_card_found = any("minCardinality" in triple[1] for triple in triple_strs)
        max_card_found = any("maxCardinality" in triple[1] for triple in triple_strs)
        self.assertFalse(min_card_found, "Should not generate minCardinality when None")
        self.assertFalse(max_card_found, "Should not generate maxCardinality when None")

    def test_only_min_cardinality(self):
        """Test restriction with only min cardinality set"""
        restriction = Restriction(
            property_type="min_only",
            min_cardinality=1
        )
        
        triples = list(restriction.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        min_card_found = any("minCardinality" in triple[1] for triple in triple_strs)
        max_card_found = any("maxCardinality" in triple[1] for triple in triple_strs)
        
        self.assertTrue(min_card_found, "Should generate minCardinality")
        self.assertFalse(max_card_found, "Should not generate maxCardinality when None")

    def test_only_max_cardinality(self):
        """Test restriction with only max cardinality set"""
        restriction = Restriction(
            property_type="max_only",
            max_cardinality=5
        )
        
        triples = list(restriction.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        min_card_found = any("minCardinality" in triple[1] for triple in triple_strs)
        max_card_found = any("maxCardinality" in triple[1] for triple in triple_strs)
        
        self.assertFalse(min_card_found, "Should not generate minCardinality when None")
        self.assertTrue(max_card_found, "Should generate maxCardinality")

    def test_zero_cardinalities(self):
        """Test restriction with zero cardinalities (explicit zeros)"""
        restriction = Restriction(
            property_type="zero_test",
            min_cardinality=0,
            max_cardinality=0
        )
        
        triples = list(restriction.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Zero cardinalities should be included (different from None)
        min_card_found = any("minCardinality" in triple[1] and "0" in triple[2] for triple in triple_strs)
        max_card_found = any("maxCardinality" in triple[1] and "0" in triple[2] for triple in triple_strs)
        
        self.assertTrue(min_card_found, "Should generate minCardinality=0")
        self.assertTrue(max_card_found, "Should generate maxCardinality=0")

    def test_common_restriction_patterns(self):
        """Test common restriction patterns used in RO-Crate schemas"""
        
        # Required single value (exactly one)
        required_single = Restriction(
            property_type="title",
            min_cardinality=1,
            max_cardinality=1
        )
        
        # Optional single value (zero or one)
        optional_single = Restriction(
            property_type="description",
            min_cardinality=0,
            max_cardinality=1
        )
        
        # Required multiple values (one or more)
        required_multiple = Restriction(
            property_type="author",
            min_cardinality=1,
            max_cardinality=None
        )
        
        # Optional multiple values (zero or more)
        optional_multiple = Restriction(
            property_type="keywords",
            min_cardinality=0,
            max_cardinality=None
        )
        
        # Test each pattern generates appropriate triples
        patterns = [required_single, optional_single, required_multiple, optional_multiple]
        
        for restriction in patterns:
            triples = list(restriction.to_triples())
            self.assertGreater(len(triples), 0, f"Restriction {restriction.property_type} should generate triples")
            
            # All should have type and onProperty
            triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
            type_found = any("Restriction" in triple[2] for triple in triple_strs)
            on_prop_found = any("onProperty" in triple[1] for triple in triple_strs)
            
            self.assertTrue(type_found, f"Restriction {restriction.property_type} should have type")
            self.assertTrue(on_prop_found, f"Restriction {restriction.property_type} should have onProperty")

    def test_custom_id(self):
        """Test restriction with custom ID"""
        custom_id = "Person_name_restriction"
        restriction = Restriction(
            id=custom_id,
            property_type="name",
            min_cardinality=1
        )
        
        self.assertEqual(restriction.id, custom_id)
        
        triples = list(restriction.to_triples())
        # The subject of triples should use the custom ID
        subjects = set(str(triple[0]) for triple in triples)
        custom_id_used = any(custom_id in subject for subject in subjects)
        self.assertTrue(custom_id_used, "Should use custom ID in triples")


if __name__ == '__main__':
    unittest.main()