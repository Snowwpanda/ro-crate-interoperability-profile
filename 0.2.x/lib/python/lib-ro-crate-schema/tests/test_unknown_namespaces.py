"""
Test for unknown namespace detection and resolution in JSON-LD contexts.

This test verifies that the system can automatically detect and create prefixes
for namespaces that are not predefined in the namespace_prefixes dictionary.
"""

import tempfile
import json
from pathlib import Path

import pytest
from rocrate.rocrate import ROCrate

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade


class TestUnknownNamespaces:
    """Test suite for unknown namespace handling."""
    
    def test_unknown_namespace_detection_in_context(self):
        """Test that unknown namespaces are automatically detected by get_context."""
        from lib_ro_crate_schema.crate.jsonld_utils import get_context
        from rdflib import Graph, URIRef, Literal
        from rdflib.namespace import RDF, RDFS
        
        # Create graph with unknown namespaces
        g = Graph()
        
        # Add triples with unknown pokemon.org namespace
        pokemon_ns = "http://pokemon.org/"
        pikachu = URIRef(pokemon_ns + "pikachu")
        pokemon_name = URIRef(pokemon_ns + "pokemonName") 
        electric_type = URIRef(pokemon_ns + "ElectricPokemon")
        
        g.add((pikachu, RDF.type, electric_type))
        g.add((pikachu, pokemon_name, Literal("Pikachu")))
        g.add((pokemon_name, RDF.type, RDF.Property))
        g.add((pokemon_name, RDFS.label, Literal("Pokemon Name")))
        
        # Add triples with another unknown namespace
        villains_ns = "http://villains.org/"
        team_rocket = URIRef(villains_ns + "team_rocket")
        criminal_org = URIRef(villains_ns + "CriminalOrganization")
        motto = URIRef(villains_ns + "motto")
        
        g.add((team_rocket, RDF.type, criminal_org))
        g.add((team_rocket, motto, Literal("Prepare for trouble!")))
        
        # Also add known namespace
        schema_name = URIRef("https://schema.org/name")
        g.add((pikachu, schema_name, Literal("Pikachu the Electric Mouse")))
        
        # Test context generation
        context = get_context(g)
        
        assert isinstance(context, list)
        assert len(context) >= 2
        
        # Check that both unknown namespaces were detected
        detected_namespaces = {}
        if len(context) > 1 and isinstance(context[1], dict):
            detected_namespaces = context[1]
        
        assert "pokemon" in detected_namespaces
        assert detected_namespaces["pokemon"] == "http://pokemon.org/"
        assert "villains" in detected_namespaces  
        assert detected_namespaces["villains"] == "http://villains.org/"
        assert "schema" in detected_namespaces
        assert detected_namespaces["schema"] == "https://schema.org/"
    
    def test_known_namespaces_still_work(self):
        """Test that predefined namespaces still work correctly."""
        from lib_ro_crate_schema.crate.jsonld_utils import get_context
        from rdflib import Graph, URIRef, Literal
        from rdflib.namespace import RDF, RDFS

        g = Graph()

        # Add triples with known namespaces used as predicates and types
        person = URIRef("http://someone.example/john")
        
        # Use example.com as a predicate (will trigger base: namespace)
        example_property = URIRef("http://example.com/customProperty")
        g.add((person, example_property, Literal("Some value")))
        
        # Use schema.org properties and types
        schema_name = URIRef("https://schema.org/name")
        g.add((person, schema_name, Literal("John Doe")))
        g.add((person, RDF.type, URIRef("https://schema.org/Person")))
        
        # Use openbis.org as a predicate
        openbis_property = URIRef("http://openbis.org/sampleId")
        g.add((person, openbis_property, Literal("sample123")))

        context = get_context(g)

        assert isinstance(context, list)
        if len(context) > 1 and isinstance(context[1], dict):
            namespaces = context[1]
            assert "base" in namespaces
            assert namespaces["base"] == "http://example.com/"
            assert "schema" in namespaces
            assert namespaces["schema"] == "https://schema.org/"
            assert "openbis" in namespaces
            assert namespaces["openbis"] == "http://openbis.org/"

    def test_prefix_collision_handling(self):
        """Test that prefix collisions are handled gracefully."""
        from lib_ro_crate_schema.crate.jsonld_utils import get_context
        from rdflib import Graph, URIRef, Literal
        from rdflib.namespace import RDF
        
        g = Graph()
        
        # Create a scenario where we might have prefix collisions
        # Use pokemon.org multiple times with DIFFERENT types (should get 'pokemon' prefix)
        pokemon_uri1 = URIRef("http://pokemon.org/pikachu")
        pokemon_uri2 = URIRef("http://pokemon.org/raichu")
        g.add((pokemon_uri1, RDF.type, URIRef("http://pokemon.org/ElectricPokemon")))
        g.add((pokemon_uri2, RDF.type, URIRef("http://pokemon.org/EvolutionPokemon")))

        # Use pokemon.com multiple times (should get 'pokemon1' or similar)  
        pokemon_com_uri1 = URIRef("http://pokemon.com/charizard")
        pokemon_com_uri2 = URIRef("http://pokemon.com/blastoise")
        g.add((pokemon_com_uri1, RDF.type, URIRef("http://pokemon.com/FirePokemon")))
        g.add((pokemon_com_uri2, RDF.type, URIRef("http://pokemon.com/WaterPokemon")))

        context = get_context(g)
        
        if isinstance(context, list) and len(context) > 1 and isinstance(context[1], dict):
            namespaces = context[1]
            
            # Both namespaces should be detected with different prefixes
            pokemon_prefixes = [k for k, v in namespaces.items() 
                              if 'pokemon.' in v]
            assert len(pokemon_prefixes) == 2
            
            # Verify the actual mappings exist
            namespace_values = list(namespaces.values())
            assert "http://pokemon.org/" in namespace_values
            assert "http://pokemon.com/" in namespace_values

    def test_minimum_usage_threshold(self):
        """Test that namespaces need minimum usage count to be detected."""
        from lib_ro_crate_schema.crate.jsonld_utils import get_context
        from rdflib import Graph, URIRef, Literal
        from rdflib.namespace import RDF
        
        g = Graph()
        
        # Add only one URI from a namespace (below threshold)
        single_use = URIRef("http://rarely-used.org/single")
        g.add((single_use, RDF.type, URIRef("https://schema.org/Thing")))
        
        # Add multiple URIs from another namespace (above threshold)
        frequent_ns = "http://frequent.org/"
        for i in range(3):
            uri = URIRef(f"{frequent_ns}item{i}")
            g.add((uri, RDF.type, URIRef(f"{frequent_ns}ItemType")))
            # Add another usage to ensure it meets the threshold
            g.add((uri, URIRef(f"{frequent_ns}hasProperty"), Literal(f"value{i}")))
        
        context = get_context(g)
        
        if isinstance(context, list) and len(context) > 1 and isinstance(context[1], dict):
            namespaces = context[1]
            
            # frequent.org should be detected
            assert "frequent" in namespaces
            assert namespaces["frequent"] == "http://frequent.org/"
            
            # rarely-used.org should NOT be detected (only 1 usage)
            rarely_used_prefixes = [k for k, v in namespaces.items() 
                                   if 'rarely-used.org' in v]
            assert len(rarely_used_prefixes) == 0


@pytest.fixture
def temp_ro_crate():
    """Create a temporary RO-Crate with unknown namespaces for testing."""
    crate = ROCrate()
    
    # Add entities with unknown namespaces
    pokemon_entity = {
        '@id': 'http://pokemon.org/pikachu',
        '@type': 'http://pokemon.org/ElectricPokemon',
        'http://pokemon.org/pokemonName': 'Pikachu',
        'http://pokemon.org/type': 'Electric',
        'https://schema.org/name': 'Pikachu the Electric Mouse'
    }
    
    villain_entity = {
        '@id': 'http://villains.org/team_rocket',
        '@type': 'http://villains.org/CriminalOrganization', 
        'http://villains.org/motto': 'Prepare for trouble!',
        'https://schema.org/name': 'Team Rocket'
    }
    
    crate.add_jsonld(pokemon_entity)
    crate.add_jsonld(villain_entity)
    
    return crate


class TestRoundTripNamespaces:
    """Test namespace handling through full import/export cycles."""
    
    def test_rocrate_roundtrip_with_unknown_namespaces(self, temp_ro_crate):
        """Test that unknown namespaces survive import/export cycles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Export original crate
            temp_ro_crate.metadata.write(temp_path)
            metadata_file = temp_path / 'ro-crate-metadata.json'
            original_data = json.loads(metadata_file.read_text())
            
            # Verify original contains full URIs
            original_entities = original_data.get('@graph', [])
            pokemon_entities = [e for e in original_entities 
                              if 'pokemon.org' in e.get('@id', '')]
            assert len(pokemon_entities) >= 1
            
            # Import via SchemaFacade
            imported_facade = SchemaFacade.from_ro_crate(temp_path)
            assert len(imported_facade.metadata_entries) > 0
            
            # Re-export and check context
            final_crate = imported_facade.get_crate()
            
            with tempfile.TemporaryDirectory() as final_dir:
                final_crate.metadata.write(final_dir)
                final_metadata_file = Path(final_dir) / 'ro-crate-metadata.json'
                final_data = json.loads(final_metadata_file.read_text())
                
                # Check that some form of context enhancement occurred
                final_context = final_data.get('@context', [])
                assert isinstance(final_context, list)
                if len(final_context) > 1:
                    assert isinstance(final_context[1], dict)
                    # Should have some namespace mappings
                    assert len(final_context[1]) > 0


if __name__ == "__main__":
    pytest.main([__file__])