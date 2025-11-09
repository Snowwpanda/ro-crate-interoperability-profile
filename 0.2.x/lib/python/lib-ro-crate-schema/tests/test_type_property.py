import unittest
import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from rdflib import RDF, RDFS, Literal, URIRef


class TestTypeProperty(unittest.TestCase):
    """Test cases for the TypeProperty class"""

    def setUp(self):
        """Set up test fixtures"""
        self.basic_property = TypeProperty(id="basicProp")
        
        self.complete_property = TypeProperty(
            id="completeProp",
            domain_includes=["Person"],
            range_includes=[LiteralType.STRING],
            ontological_annotations=["https://schema.org/name"],
            comment="A complete property for testing",
            label="Complete Property",
            required=True
        )

    def test_property_creation(self):
        """Test basic TypeProperty object creation"""
        self.assertEqual(self.basic_property.id, "basicProp")
        self.assertEqual(self.basic_property.domain_includes, [])
        self.assertEqual(self.basic_property.range_includes, [])
        self.assertIsNone(self.basic_property.required)

    def test_fluent_api(self):
        """Test fluent API methods"""
        prop = TypeProperty(id="fluentTest")
        result = (prop
                 .setLabel("Test Label")
                 .setComment("Test Comment")
                 .setTypes([LiteralType.STRING, LiteralType.INTEGER])
                 .setRequired(True)
                 .setOntologicalAnnotations(["http://example.org/prop"]))
        
        # Check method chaining works
        self.assertEqual(result, prop)
        
        # Check values were set
        self.assertEqual(prop.label, "Test Label")
        self.assertEqual(prop.comment, "Test Comment")
        self.assertTrue(prop.required)
        self.assertEqual(prop.range_includes, [LiteralType.STRING, LiteralType.INTEGER])
        self.assertEqual(prop.ontological_annotations, ["http://example.org/prop"])

    def test_add_type(self):
        """Test adding single type to range"""
        prop = TypeProperty(id="testProp")
        prop.addType(LiteralType.STRING)
        prop.addType("CustomType")
        
        self.assertIn(LiteralType.STRING, prop.range_includes)
        self.assertIn("CustomType", prop.range_includes)

    def test_java_api_compatibility(self):
        """Test Java API compatibility methods"""
        self.assertEqual(self.complete_property.getId(), "completeProp")
        self.assertEqual(self.complete_property.getLabel(), "Complete Property")
        self.assertEqual(self.complete_property.getComment(), "A complete property for testing")
        self.assertEqual(self.complete_property.getDomain(), ["Person"])
        self.assertEqual(self.complete_property.getRange(), [LiteralType.STRING])
        self.assertEqual(self.complete_property.getOntologicalAnnotations(), ["https://schema.org/name"])

    def test_cardinality_methods(self):
        """Test cardinality getter methods"""
        # Required property
        required_prop = TypeProperty(id="required", required=True)
        self.assertEqual(required_prop.get_min_cardinality(), 1)
        self.assertEqual(required_prop.get_max_cardinality(), 1)
        
        # Optional property
        optional_prop = TypeProperty(id="optional", required=False)
        self.assertEqual(optional_prop.get_min_cardinality(), 0)
        self.assertEqual(optional_prop.get_max_cardinality(), 1)
        
        # Unspecified property (defaults to optional)
        unspecified_prop = TypeProperty(id="unspecified")
        self.assertEqual(unspecified_prop.get_min_cardinality(), 0)
        self.assertEqual(unspecified_prop.get_max_cardinality(), 1)

    def test_to_triples(self):
        """Test RDF triple generation"""
        triples = list(self.complete_property.to_triples())
        
        # Should generate multiple triples
        self.assertGreater(len(triples), 0)
        
        # Convert to string representation for easier testing
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Check for essential triples
        type_triple_found = any("Property" in triple[2] for triple in triple_strs)
        self.assertTrue(type_triple_found, "Should generate rdf:Property type triple")
        
        label_triple_found = any("label" in triple[1] for triple in triple_strs)
        self.assertTrue(label_triple_found, "Should generate rdfs:label triple")
        
        domain_triple_found = any("domainIncludes" in triple[1] for triple in triple_strs)
        self.assertTrue(domain_triple_found, "Should generate domainIncludes triple")

    def test_range_includes_xsd_types(self):
        """Test handling of XSD data types in range_includes"""
        prop = TypeProperty(
            id="xsdTest",
            range_includes=["xsd:string", "xsd:integer", "xsd:boolean"]
        )
        
        triples = list(prop.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Should convert xsd: prefixes to full URIs
        xsd_string_found = any("XMLSchema#string" in triple[2] for triple in triple_strs)
        self.assertTrue(xsd_string_found, "Should convert xsd:string to full URI")

    def test_range_includes_base_types(self):
        """Test handling of base: prefixed types in range_includes"""
        prop = TypeProperty(
            id="baseTest",
            range_includes=["base:CustomType"]
        )
        
        triples = list(prop.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Should handle base: prefixed types
        base_type_found = any("CustomType" in triple[2] for triple in triple_strs)
        self.assertTrue(base_type_found, "Should handle base: prefixed types")

    def test_ontological_annotations(self):
        """Test ontological annotation handling"""
        prop = TypeProperty(
            id="ontoTest",
            ontological_annotations=["https://schema.org/name", "http://purl.org/dc/terms/title"]
        )
        
        triples = list(prop.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Should generate owl:equivalentProperty triples
        equiv_prop_found = any("equivalentProperty" in triple[1] for triple in triple_strs)
        self.assertTrue(equiv_prop_found, "Should generate owl:equivalentProperty triples")

    def test_empty_property(self):
        """Test property with minimal configuration"""
        empty_prop = TypeProperty(id="minimal")
        triples = list(empty_prop.to_triples())
        
        # Should at least generate the property type declaration
        self.assertGreater(len(triples), 0)
        
        # Should be an rdf:Property
        type_triple_found = any("Property" in str(triple) for triple in triples)
        self.assertTrue(type_triple_found)

    def test_multiple_domains(self):
        """Test property with multiple domain classes"""
        prop = TypeProperty(
            id="multiDomain",
            domain_includes=["Person", "Organization", "Event"]
        )
        
        triples = list(prop.to_triples())
        triple_strs = [(str(s), str(p), str(o)) for s, p, o in triples]
        
        # Should generate domainIncludes for each domain
        person_domain = any("Person" in triple[2] and "domainIncludes" in triple[1] for triple in triple_strs)
        org_domain = any("Organization" in triple[2] and "domainIncludes" in triple[1] for triple in triple_strs)
        event_domain = any("Event" in triple[2] and "domainIncludes" in triple[1] for triple in triple_strs)
        
        self.assertTrue(person_domain, "Should include Person in domain")
        self.assertTrue(org_domain, "Should include Organization in domain")
        self.assertTrue(event_domain, "Should include Event in domain")


if __name__ == '__main__':
    unittest.main()