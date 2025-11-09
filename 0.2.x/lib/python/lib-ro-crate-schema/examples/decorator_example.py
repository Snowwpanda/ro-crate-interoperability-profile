"""
Example demonstrating the decorator-based model registration system.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.decorators import ro_crate_schema, Field
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade  
from lib_ro_crate_schema.crate.schema_registry import get_schema_registry


# Example 1: Basic model with ontology annotations (required and optional fields)
@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    """A person in the research project"""
    # Required fields (minCardinality: 1)
    name: str = Field(ontology="https://schema.org/name", comment="Person's full name")
    email: str = Field(ontology="https://schema.org/email", comment="Contact email address")
    
    # Optional fields (minCardinality: 0)
    orcid: Optional[str] = Field(default=None, ontology="https://orcid.org/", comment="ORCID identifier")
    phone: Optional[str] = Field(default=None, ontology="https://schema.org/telephone", comment="Phone number")
    affiliation: Optional[str] = Field(default=None, ontology="https://schema.org/affiliation", comment="Institution affiliation")


# Example 2: Model with relationships and mixed required/optional fields
@ro_crate_schema(ontology="https://schema.org/Dataset")
class Dataset(BaseModel):
    """A research dataset"""
    # Required fields (minCardinality: 1)
    title: str = Field(ontology="https://schema.org/name", comment="Dataset title")
    description: str = Field(ontology="https://schema.org/description", comment="Dataset description")
    authors: List[Person] = Field(ontology="https://schema.org/author", comment="Dataset authors")
    created_date: datetime = Field(ontology="https://schema.org/dateCreated", comment="Creation date")
    
    # Optional fields (minCardinality: 0)
    keywords: Optional[List[str]] = Field(default=None, ontology="https://schema.org/keywords", comment="Research keywords")
    version: Optional[str] = Field(default=None, ontology="https://schema.org/version", comment="Dataset version")
    license: Optional[str] = Field(default=None, ontology="https://schema.org/license", comment="License information")


# Example 3: Model with institutional information  
@ro_crate_schema(ontology="https://schema.org/Organization")
class Institution(BaseModel):
    """Research institution or organization"""
    name: str = Field(ontology="https://schema.org/name", comment="Institution name")
    country: str = Field(comment="Country where institution is located")
    website: Optional[str] = Field(default=None, comment="Institution website")


def example_usage():
    """Demonstrate the complete workflow"""
    
    print("=== Decorator-based RO-Crate Schema Generation ===")
    print()
    
    # 1. Show registered models (automatically registered by decorators)
    registry = get_schema_registry()
    
    print("Registered models:")
    for model_name, type_template in registry.get_all_type_templates().items():
        print(f"  - {model_name}: {type_template.ontology}")
        for prop_info in type_template.type_properties:
            print(f"    * {prop_info.name}: {prop_info.rdf_type} (ontology: {prop_info.ontology})")
    print()
    
    # 2. Create schema facade and add all registered models
    facade = SchemaFacade()
    facade.add_all_registered_models()
    
    print(f"Schema contains {len(facade.types)} types:")
    for type_obj in facade.types:
        print(f"  - {type_obj.id}: {type_obj.ontological_annotations}")
    print()
    
    # 3. Create model instances and add them as metadata
    person1 = Person(
        name="Dr. Jane Smith",
        email="jane.smith@university.edu", 
        orcid="0000-0000-0000-0001"
    )
    
    person2 = Person(
        name="Prof. John Doe",
        email="john.doe@institute.org"
    )
    
    dataset = Dataset(
        title="Climate Change Impact Study",
        description="Analysis of climate data from 2000-2023",
        authors=[person1, person2],
        created_date=datetime(2024, 1, 15),
        keywords=["climate", "environment", "data analysis"]
    )
    
    # Add instances as metadata entries
    facade.add_model_instance(person1, "jane_smith")
    facade.add_model_instance(person2, "john_doe")
    facade.add_model_instance(dataset, "climate_study_2024")
    
    print(f"Metadata contains {len(facade.metadata_entries)} entries:")
    for entry in facade.metadata_entries:
        print(f"  - {entry.id} ({entry.class_id})")
        print(f"    Properties: {entry.properties}")
        print(f"    References: {entry.references}")
    print()
    
    # 4. Generate RDF graph
    graph = facade.to_graph()
    print(f"Generated RDF graph with {len(graph)} triples")
    print()
    print("Sample triples:")
    for i, (s, p, o) in enumerate(graph):
        if i < 10:  # Show first 10 triples
            print(f"  {s} {p} {o}")
    print()
    
    # 5. Convert to RO-Crate
    from lib_ro_crate_schema.crate.jsonld_utils import add_schema_to_crate
    from rocrate.rocrate import ROCrate
    import json
    from pathlib import Path
    
    print("🔄 Adding schema and metadata to RO-Crate...")
    crate = ROCrate()
    crate.name = "Decorator Example RO-Crate"
    crate.description = "Generated using decorator-based schema registration"
    
    final_crate = add_schema_to_crate(facade, crate)
    
    # Get JSON representation by writing to temp directory
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        final_crate.write(temp_dir)
        metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
        with open(metadata_file, 'r') as f:
            final_crate_json = json.load(f)
    
    # Save to file
    output_path = Path("ro-crate-metadata.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_crate_json, f, indent=2)
    
    print(f"✅ RO-Crate saved to: {output_path.absolute()}")
    print(f"📊 Total entities in @graph: {len(final_crate_json['@graph'])}")
    print()
    
    # Show entity types summary
    entity_types = {}
    for entity in final_crate_json["@graph"]:
        entity_type = entity.get("@type", "Unknown")
        if isinstance(entity_type, list):
            for t in entity_type:
                entity_types[t] = entity_types.get(t, 0) + 1
        else:
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    print("📋 Entity types in RO-Crate:")
    for entity_type, count in entity_types.items():
        print(f"  - {entity_type}: {count}")
    print()
    
    # Show context
    context = final_crate_json["@context"]
    print(f"🔗 RO-Crate @context: {context}")
    print()
    
    print("🎯 Key Features Demonstrated:")
    print("  ✓ Pydantic models → RDFS schema")
    print("  ✓ Ontology annotations (schema.org, ORCID)")
    print("  ✓ Model instances → RDF metadata")
    print("  ✓ Proper RO-Crate integration")
    print("  ✓ JSON-LD context management")
    print("  ✓ Schema embedding in ro-crate-metadata.json")

    return facade, final_crate_json


if __name__ == "__main__":
    example_usage()