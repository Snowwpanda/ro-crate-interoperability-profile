import unittest
import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.restriction import Restriction
from rdflib import RDFS, RDF, OWL, Literal, URIRef


class TestType(unittest.TestCase):
    """Test cases for the Type class"""

    def setUp(self):
        """Set up test fixtures"""
        self.basic_type = Type(id="TestType")
        
        # Create a property for testing
        self.test_property = TypeProperty(
            id="testProperty",
            range_includes=[LiteralType.STRING],
            required=True
        )
        
        # Create a complete type with all features
        self.complete_type = Type(
            id="Person",
            subclass_of=["https://schema.org/Thing"],
            ontological_annotations=["https://schema.org/Person"],
            rdfs_property=[self.test_property],
            comment="A person entity",
            label="Person"
        )

    def test_type_creation(self):
        """Test basic Type object creation"""
        self.assertEqual(self.basic_type.id, "TestType")
        self.assertIsInstance(self.basic_type.subclass_of, list)
        self.assertEqual(self.basic_type.subclass_of, ["https://schema.org/Thing"])
        
    def test_fluent_api(self):
        """Test fluent API methods"""
        type_obj = Type(id="FluentTest")
        result = (type_obj
                 .setLabel("Test Label")
                 .setComment("Test Comment")
                 .addProperty(self.test_property)
                 .setOntologicalAnnotations(["http://example.org/TestClass"]))
        
        # Check method chaining works
        self.assertEqual(result, type_obj)
        
        # Check values were set
        self.assertEqual(type_obj.label, "Test Label")
        self.assertEqual(type_obj.comment, "Test Comment")
        self.assertEqual(type_obj.ontological_annotations, ["http://example.org/TestClass"])
        self.assertIn(self.test_property, type_obj.rdfs_property)

    def test_java_api_compatibility(self):
        """Test Java API compatibility methods"""
        self.assertEqual(self.complete_type.getId(), "Person")
        self.assertEqual(self.complete_type.getLabel(), "Person")
        self.assertEqual(self.complete_type.getComment(), "A person entity")
        self.assertEqual(self.complete_type.getSubClassOf(), ["https://schema.org/Thing"])
        self.assertEqual(self.complete_type.getOntologicalAnnotations(), ["https://schema.org/Person"])

    def test_get_restrictions(self):
        """Test restriction generation from properties"""
        restrictions = self.complete_type.get_restrictions()
        
        self.assertIsInstance(restrictions, list)
        self.assertTrue(len(restrictions) >= 1)
        
        # Find the restriction for our test property
        test_prop_restriction = None
        for restriction in restrictions:
            if restriction.property_type == "testProperty":
                test_prop_restriction = restriction
                break
        
        self.assertIsNotNone(test_prop_restriction)
        self.assertEqual(test_prop_restriction.min_cardinality, 1)  # required=True

    def test_to_triples(self):
        """Test RDF triple generation"""
        triples = list(self.complete_type.to_triples())
        
        # Should generate multiple triples
        self.assertGreater(len(triples), 0)
        
        # Convert to list of tuples for easier testing
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Check for essential triples - look for Class in the object
        type_triple_found = any("Class" in triple[2] for triple in triple_strs)
        self.assertTrue(type_triple_found, "Should generate rdfs:Class type triple")
        
        label_triple_found = any("label" in triple[1] for triple in triple_strs)
        self.assertTrue(label_triple_found, "Should generate rdfs:label triple")

    def test_empty_type(self):
        """Test type with minimal configuration"""
        empty_type = Type(id="MinimalType")
        triples = list(empty_type.to_triples())
        
        # Should at least generate the class type declaration
        self.assertGreater(len(triples), 0)

    def test_property_addition(self):
        """Test adding properties to a type"""
        type_obj = Type(id="TestType")
        
        prop1 = TypeProperty(id="prop1", range_includes=[LiteralType.STRING])
        prop2 = TypeProperty(id="prop2", range_includes=[LiteralType.INTEGER])
        
        type_obj.addProperty(prop1).addProperty(prop2)
        
        self.assertEqual(len(type_obj.rdfs_property), 2)
        self.assertIn(prop1, type_obj.rdfs_property)
        self.assertIn(prop2, type_obj.rdfs_property)

    def test_custom_restrictions(self):
        """Test type with custom restrictions"""
        custom_restriction = Restriction(
            property_type="customProp",
            min_cardinality=2,
            max_cardinality=5
        )
        
        type_obj = Type(
            id="RestrictedType",
            restrictions=[custom_restriction]
        )
        
        restrictions = type_obj.get_restrictions()
        self.assertIn(custom_restriction, restrictions)


if __name__ == '__main__':
    unittest.main()