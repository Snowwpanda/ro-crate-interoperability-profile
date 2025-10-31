#!/usr/bin/env python3
"""
Simple test to see how unknown namespaces are handled by get_context function.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lib_ro_crate_schema.crate.jsonld_utils import get_context
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS


def create_graph_with_unknown_namespaces():
    """Create an RDF graph with unknown namespaces."""
    g = Graph()
    
    # Add triples with unknown pokemon.org namespace
    pokemon_ns = "http://pokemon.org/"
    pikachu = URIRef(pokemon_ns + "pikachu")
    pokemon_name = URIRef(pokemon_ns + "pokemonName") 
    electric_type = URIRef(pokemon_ns + "ElectricPokemon")
    
    # Add some triples
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
    
    # Also add some known namespaces for comparison
    schema_name = URIRef("https://schema.org/name")
    g.add((pikachu, schema_name, Literal("Pikachu the Electric Mouse")))
    
    # Add example.com namespace (base namespace in predefined list)
    example_person = URIRef("http://example.com/trainer")
    example_name = URIRef("http://example.com/trainerName")
    g.add((example_person, example_name, Literal("Ash Ketchum")))
    g.add((example_name, RDF.type, RDF.Property))
    
    return g


def main():
    print("🔍 TESTING get_context() WITH UNKNOWN NAMESPACES")
    print("=" * 55)
    
    # Create graph with unknown namespaces
    g = create_graph_with_unknown_namespaces()
    
    print("📊 Graph Statistics:")
    print(f"   Total triples: {len(g)}")
    
    print("\n🔍 URIs in the graph:")
    all_uris = set()
    for s, p, o in g:
        for uri in [str(s), str(p), str(o)]:
            if uri.startswith('http'):
                all_uris.add(uri)
    
    # Group by namespace
    namespaces = {}
    for uri in sorted(all_uris):
        if 'pokemon.org' in uri:
            namespaces.setdefault('pokemon.org', []).append(uri)
        elif 'villains.org' in uri:
            namespaces.setdefault('villains.org', []).append(uri)
        elif 'schema.org' in uri:
            namespaces.setdefault('schema.org', []).append(uri)
        elif 'example.com' in uri:
            namespaces.setdefault('example.com', []).append(uri)
        else:
            namespaces.setdefault('other', []).append(uri)
    
    for ns, uris in namespaces.items():
        print(f"\n   {ns}:")
        for uri in uris[:3]:  # Show first 3
            print(f"     {uri}")
        if len(uris) > 3:
            print(f"     ... and {len(uris) - 3} more")
    
    # Test get_context function
    print(f"\n🎯 Testing get_context() function:")
    context = get_context(g)
    
    print("📋 Generated Context:")
    if isinstance(context, list):
        for i, ctx_layer in enumerate(context):
            if isinstance(ctx_layer, str):
                print(f"   Layer {i}: \"{ctx_layer}\"")
            else:
                print(f"   Layer {i}:")
                for prefix, uri in sorted(ctx_layer.items()):
                    print(f"      \"{prefix}\": \"{uri}\"")
    else:
        print(f"   Single context: {context}")
    
    # Analyze what happened
    print(f"\n🧪 Analysis:")
    detected_namespaces = set()
    if isinstance(context, list) and len(context) > 1:
        for ctx in context[1:]:
            if isinstance(ctx, dict):
                detected_namespaces.update(ctx.values())
    
    test_namespaces = [
        ('pokemon.org', 'http://pokemon.org/'),
        ('villains.org', 'http://villains.org/'),
        ('schema.org', 'https://schema.org/'),
        ('example.com', 'http://example.com/')
    ]
    
    for ns_name, ns_uri in test_namespaces:
        if ns_uri in detected_namespaces:
            print(f"   ✅ {ns_name}: DETECTED")
        else:
            print(f"   ❌ {ns_name}: NOT DETECTED")
    
    print(f"\n🎮 Conclusion:")
    unknown_detected = any(ns in detected_namespaces for _, ns in test_namespaces[:2])
    if unknown_detected:
        print(f"   🎉 Unknown namespaces are automatically detected!")
    else:
        print(f"   ❌ Unknown namespaces are NOT automatically detected")
        print(f"   ➡️  Only predefined namespaces in namespace_prefixes are recognized")


if __name__ == "__main__":
    main()