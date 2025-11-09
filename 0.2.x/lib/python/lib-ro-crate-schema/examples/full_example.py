#!/usr/bin/env python3
"""
Comprehensive RO-Crate Schema Library Demonstration

This example showcases the full capabilities of the RO-Crate schema library through
a complex scientific workflow involving OpenBIS data management, chemical synthesis, object modification with round-trip persistence.

Features demonstrated:
- Complex nested object hierarchies (Project → Space → Collections/Equipment)
- Self-referential relationships (molecules containing other molecules)
- Mixed ontology namespaces (OpenBIS custom + schema.org)
- Dynamic experimental workflow simulation
- Large-scale RDF generation and serialization
- Round-trip fidelity with state modifications
- Real-world scientific data modeling

Run with: uv run python examples/full_example.py
"""

import json
from math import e
import sys
import csv
import tempfile
from pathlib import Path
from datetime import datetime
from tkinter import E
from typing import List, Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic import BaseModel
from lib_ro_crate_schema.crate.decorators import ro_crate_schema, Field
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade


# Removed print_section function - using direct print statements instead


# ============================================================================
# MODEL DEFINITIONS
# ============================================================================

@ro_crate_schema(ontology="http://openbis.org/Project")
class Project(BaseModel):
    """OpenBIS research project"""
    code: str = Field(json_schema_extra={"comment": "Unique project identifier"})
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    description: str = Field(json_schema_extra={"ontology": "https://schema.org/description"})
    created_date: datetime = Field(json_schema_extra={"ontology": "https://schema.org/dateCreated"})
    space: Optional['Space'] = Field(default=None, json_schema_extra={"ontology": "http://openbis.org/hasSpace"})


@ro_crate_schema(ontology="http://openbis.org/Space")
class Space(BaseModel):
    """OpenBIS laboratory space"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    description: str = Field(json_schema_extra={"ontology": "https://schema.org/description"})
    created_date: datetime = Field(json_schema_extra={"ontology": "https://schema.org/dateCreated"})
    collections: List['Collection'] = Field(default=[], json_schema_extra={"ontology": "http://openbis.org/hasCollection"})

@ro_crate_schema(ontology="http://openbis.org/Collection")
class Collection(BaseModel):
    """OpenBIS sample/data collection"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    sample_type: str = Field(json_schema_extra={"comment": "Type of samples stored"})
    storage_conditions: str = Field(json_schema_extra={"comment": "Storage requirements"})
    created_date: datetime = Field(json_schema_extra={"ontology": "https://schema.org/dateCreated"})
    contains: List[Any] = Field(default=[], json_schema_extra={"comment": "Entities contained in the collection"})


@ro_crate_schema(ontology="http://openbis.org/Equipment")
class Equipment(BaseModel):
    """Laboratory equipment with optional nesting"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    model: str = Field(json_schema_extra={"comment": "Equipment model/version"})
    serial_number: str = Field(json_schema_extra={"ontology": "https://schema.org/serialNumber"})
    created_date: datetime = Field(json_schema_extra={"ontology": "https://schema.org/dateCreated"})
    parent_equipment: Optional['Equipment'] = Field(default=None, json_schema_extra={"ontology": "https://schema.org/isPartOf"})
    configuration: Dict[str, Any] = Field(default={}, json_schema_extra={"comment": "Equipment configuration parameters"})


@ro_crate_schema(ontology="https://schema.org/ChemicalSubstance")
class Molecule(BaseModel):
    """Chemical compound with SMILES notation"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    smiles: str = Field(json_schema_extra={"comment": "SMILES notation for chemical structure"})
    molecular_weight: float = Field(json_schema_extra={"comment": "Molecular weight in g/mol"})
    contains_molecules: List['Molecule'] = Field(default=[], json_schema_extra={"ontology": "https://schema.org/hasPart"})
    cas_number: Optional[str] = Field(default=None, json_schema_extra={"comment": "CAS Registry Number"})
    created_date: datetime = Field(json_schema_extra={"ontology": "https://schema.org/dateCreated"})
    experimental_notes: Optional[str] = Field(default=None, json_schema_extra={"comment": "Lab notes or modifications"})


@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    """Research author/scientist"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    orcid: str = Field(json_schema_extra={"ontology": "https://schema.org/identifier"})
    email: str = Field(json_schema_extra={"ontology": "https://schema.org/email"})
    affiliation: 'Organization' = Field(json_schema_extra={"ontology": "https://schema.org/affiliation"})
    colleagues: List['Person'] = Field(default=[], json_schema_extra={"ontology": "https://schema.org/colleague"})


@ro_crate_schema(ontology="https://schema.org/Organization")
class Organization(BaseModel):
    """Research institution"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    country: str = Field(json_schema_extra={"ontology": "https://schema.org/addressCountry"})
    website: str = Field(json_schema_extra={"ontology": "https://schema.org/url"})


@ro_crate_schema(ontology="https://schema.org/ScholarlyArticle")
class Publication(BaseModel):
    """Scientific publication"""
    title: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    authors: List[Person] = Field(json_schema_extra={"ontology": "https://schema.org/author"})
    molecules: List[Molecule] = Field(json_schema_extra={"ontology": "https://schema.org/mentions"})
    equipment: List[Equipment] = Field(json_schema_extra={"ontology": "https://schema.org/instrument"})
    organization: Organization = Field(json_schema_extra={"ontology": "https://schema.org/publisher"})
    doi: str = Field(json_schema_extra={"ontology": "https://schema.org/identifier"})
    publication_date: datetime = Field(json_schema_extra={"ontology": "https://schema.org/datePublished"})


def create_initial_data():
    """Create all initial model instances"""
    
    print("\n🎯 PHASE 1: INITIAL DATA CREATION")
    print("=" * 40)
    
    # Organization
    empa = Organization(
        name="Swiss Federal Laboratories for Materials Science and Technology (Empa)",
        country="Switzerland", 
        website="https://www.empa.ch"
    )
    
    # People (with circular colleague relationships)
    # First create persons without colleagues
    sarah = Person(
        name="Dr. Sarah Chen",
        orcid="0000-0002-1234-5678",
        email="sarah.chen@empa.ch",
        affiliation=empa,
        colleagues=[]
    )
    
    marcus = Person(
        name="Prof. Marcus Weber", 
        orcid="0000-0003-8765-4321",
        email="marcus.weber@empa.ch",
        affiliation=empa,
        colleagues=[]
    )
    
    # Now establish circular colleague relationships
    # This tests how the system handles circular imports in the schema
    sarah = sarah.model_copy(update={'colleagues': [marcus]})
    marcus = marcus.model_copy(update={'colleagues': [sarah]})
    
    # Equipment (nested)
    mass_spec = Equipment(
        name="Agilent 7890A GC-MS",
        model="7890A",
        serial_number="DE43151234",
        created_date=datetime(2023, 1, 15),
        configuration={
            "ionization_mode": "EI",
            "mass_range_min": 50,
            "mass_range_max": 500,
            "resolution": "unit_mass",
            "detector_voltage": 1200
        }
    )
    
    reactor = Equipment(
        name="FlowSyn Reactor",
        model="v2.1", 
        serial_number="FSR-2024-001",
        created_date=datetime(2023, 2, 1),
        parent_equipment=mass_spec,  # Mass spec is part of reactor system
        configuration={
            "max_temperature_celsius": 250,
            "max_pressure_bar": 10,
            "flow_rate_ml_per_min": 5,
            "volume_ml": 50,
            "heating_method": "microwave"
        }
    )
    
    # Collections
    molecules_collection = Collection(
        name="Molecular Library",
        sample_type="Chemical compounds",
        storage_conditions="-20°C, inert atmosphere",
        created_date=datetime(2023, 3, 1),
        contains=[]  # Will populate later
    )
    
    lab_equipment = Collection(
        name="Laboratory Equipment",
        sample_type="Analytical instruments",
        storage_conditions="Room temperature, calibrated monthly",
        created_date=datetime(2023, 2, 15),
        contains=[reactor, mass_spec]  # Equipment collection contains these items
    )
    
    # Molecules (with complex relationships)
    benzene = Molecule(
        name="Benzene",
        smiles="c1ccccc1", 
        molecular_weight=78.11,
        cas_number="71-43-2",
        created_date=datetime(2024, 1, 10)
    )
    
    toluene = Molecule(
        name="Toluene",
        smiles="Cc1ccccc1",
        molecular_weight=92.14,
        cas_number="108-88-3", 
        created_date=datetime(2024, 1, 12)
    )
    
    phenol = Molecule(
        name="Phenol",
        smiles="c1ccc(cc1)O",
        molecular_weight=94.11,
        cas_number="108-95-2",
        created_date=datetime(2024, 1, 15)
    )
    
    aniline = Molecule(
        name="Aniline",
        smiles="c1ccc(cc1)N",
        molecular_weight=93.13,
        cas_number="62-53-3",
        created_date=datetime(2024, 1, 18)
    )
    
    # Complex polymer containing other molecules
    complex_polymer = Molecule(
        name="Benzene-Toluene Polymer",
        smiles="[*]c1ccccc1[*].[*]Cc1ccccc1[*]",  # Polymer SMILES
        molecular_weight=340.45,
        contains_molecules=[benzene, toluene],  # Self-reference
        created_date=datetime(2024, 2, 1)
    )
    
    # Add molecules to collection
    molecules_collection.contains.extend([benzene, toluene, phenol, aniline, complex_polymer])

    # OpenBIS hierarchy
    science_space = Space(
        name="Advanced Materials Laboratory", 
        description="State-of-the-art facility for nanomaterial synthesis and characterization",
        created_date=datetime(2023, 1, 1),
        collections=[molecules_collection, lab_equipment]
    )
    
    openbis_project = Project(
        code="NANO-2024",
        name="Nanocomposite Materials Research", 
        description="Development of advanced nanocomposite materials for industrial applications",
        created_date=datetime(2024, 1, 1),
        space=science_space
    )
    
    # Publication tying everything together
    publication = Publication(
        title="Advanced Nanocomposite Materials: From Molecular Design to Industrial Applications",
        authors=[sarah, marcus],
        molecules=[benzene, toluene, phenol, aniline, complex_polymer],
        equipment=[reactor, mass_spec],
        organization=empa,
        doi="10.1021/acs.nanolett.2024.12345",
        publication_date=datetime(2024, 6, 15)
    )
    
    return {
        'openbis_project': openbis_project,
        'science_space': science_space, 
        'molecules_collection': molecules_collection,
        'lab_equipment': lab_equipment,
        'reactor': reactor,
        'mass_spec': mass_spec,
        'benzene': benzene,
        'toluene': toluene, 
        'phenol': phenol,
        'aniline': aniline,
        'complex_polymer': complex_polymer,
        'sarah': sarah,
        'marcus': marcus,
        'empa': empa,
        'publication': publication
    }


class MoleculeModel:  # Alias for sake of this example
    pass

# EquipmentModel = Equipment  # Alias for clarity

def experiment(reactant1, reactant2, catalyst, equipment) -> tuple[dict, Path]:
    """
    Simulate chemical synthesis experiment and create observation file
    
    Creates a new product molecule by combining reactants and modifies
    the original reactants with experimental notes. Also generates a CSV
    file with experimental observations.
    
    Args:
        reactant1: Primary reactant molecule  
        reactant2: Secondary reactant molecule
        catalyst: Catalytic molecule (unchanged)
        equipment: Equipment used for reaction
        
    Returns:
        Tuple of (new product molecule, path to observations CSV file)
    """
    
    print("\n🔹 EXPERIMENTAL SYNTHESIS")
    print(f"  Reactants: {reactant1.name} + {reactant2.name}")
    print(f"  Catalyst: {catalyst.name}")
    print(f"  Equipment: {equipment.name}")
    
    # Experimental parameters and observations
    experiment_time = datetime.now()
    
    # Create product molecule with combined SMILES
    # Simple concatenation for demo (real chemistry would be more complex)
    product_smiles = f"({reactant1.smiles}).({reactant2.smiles})"
    product_mw = reactant1.molecular_weight + reactant2.molecular_weight
    
    product_dict = {
        "name": f"{reactant1.name}-{reactant2.name} Adduct",
        "smiles": product_smiles,
        "molecular_weight": product_mw,
        "contains_molecules": [reactant1, reactant2],  # Names instead of objects
        "created_date": experiment_time.isoformat(),
        "experimental_notes": f"Synthesized via {catalyst.name} catalysis using {equipment.name}"
    }
    
    # Get sample experimental observations CSV file (located in same folder as this scipt)
    csv_path = Path(__file__).parent / "experimental_observations.csv"

    # Check for file
    if not csv_path.exists():
        print(f"  ⚠️  Warning: Observations CSV file not found at {csv_path}. Skipping file adding.")
    else:
        print(f"  📁  Found observations CSV file at: {csv_path}")
    
    # Modify original reactants with experimental data
    reactant1.experimental_notes = f"Consumed 0.5 mol in synthesis reaction at {experiment_time.strftime('%Y-%m-%d %H:%M')}"
    reactant2.experimental_notes = f"Partially consumed, 0.3 mol remaining after reaction"
    
    print(f"  Product: {product_dict['name']}")
    print(f"  Product SMILES: {product_dict['smiles']}")
    
    return product_dict, csv_path


def analyze_rocrate_changes(initial_path: Path, final_path: Path):
    """Compare initial and final RO-Crate files"""
    
    print("\n🔹 RO-CRATE COMPARISON ANALYSIS")
    
    with open(initial_path / "ro-crate-metadata.json", 'r') as f:
        initial_data = json.load(f)
    
    with open(final_path / "ro-crate-metadata.json", 'r') as f:
        final_data = json.load(f)
    
    initial_entities = len(initial_data["@graph"])
    final_entities = len(final_data["@graph"])
    
    print(f"  📊 Initial entities: {initial_entities}")
    print(f"  📊 Final entities: {final_entities}")
    print(f"  📈 Change: +{final_entities - initial_entities} entities")
    
    # Count entity types
    def count_types(data):
        types = {}
        for entity in data["@graph"]:
            entity_type = entity.get("@type", "Unknown")
            if isinstance(entity_type, list):
                for t in entity_type:
                    types[t] = types.get(t, 0) + 1
            else:
                types[entity_type] = types.get(entity_type, 0) + 1
        return types
    
    initial_types = count_types(initial_data)
    final_types = count_types(final_data)
    
    print("\n  📋 Entity type changes:")
    all_types = set(initial_types.keys()) | set(final_types.keys())
    for entity_type in sorted(all_types):
        initial_count = initial_types.get(entity_type, 0)
        final_count = final_types.get(entity_type, 0)
        if initial_count != final_count:
            print(f"    {entity_type}: {initial_count} → {final_count} ({final_count - initial_count:+d})")
        else:
            print(f"    {entity_type}: {initial_count} (unchanged)")


def main():
    """Execute the complete workflow demonstration"""
    
    print("🧪 COMPREHENSIVE RO-CRATE SCHEMA WORKFLOW DEMONSTRATION")
    print("=" * 80)
    print("This demo showcases complex scientific data modeling, experimental workflows,")
    print("and dynamic object modification with full round-trip persistence.")
    
    # ========================================================================
    # PHASE 1: INITIAL SETUP
    # ========================================================================
    
    print("\n🎯 Creating Initial Schema and Data")
    print("=" * 40)
    
    # Create all instances
    instances = create_initial_data()
    
    print(f"  ✅ Created {len(instances)} model instances")
    print("  📋 Instance types:")
    type_counts = {}
    for instance in instances.values():
        type_name = type(instance).__name__
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
    
    for type_name, count in sorted(type_counts.items()):
        print(f"    - {type_name}: {count}")
    
    print(f"\n  🔄 Circular Relationship Test:")
    sarah_instance = instances['sarah']
    marcus_instance = instances['marcus']
    print(f"    - Sarah Chen has {len(sarah_instance.colleagues)} colleague(s): {[c.name for c in sarah_instance.colleagues]}")
    print(f"    - Marcus Weber has {len(marcus_instance.colleagues)} colleague(s): {[c.name for c in marcus_instance.colleagues]}")
    
    # Build schema facade
    facade = SchemaFacade()
    facade.add_all_registered_models()
    
    print(f"\n  📊 Schema: {len(facade.types)} types registered")
    
    # Add all instances
    for instance_id, instance in instances.items():
        facade.add_model_instance(instance, instance_id)
    
    print(f"  📦 Added {len(facade.metadata_entries)} metadata entries")
    
    # Generate RDF
    rdf_graph = facade.to_graph()
    print(f"  🕸️  Generated {len(rdf_graph)} RDF triples")
    
    # Export initial state
    print("\n🔹 Exporting Initial RO-Crate")
    import os
    output_dir = "output_crates"
    os.makedirs(output_dir, exist_ok=True)
    initial_path = os.path.join(output_dir, "full_example_initial")
    facade.write(
        destination=initial_path,
        name="Complex Scientific Workflow - Initial State",
        description="Initial RO-Crate before experimental modifications",
        license="MIT"
    )
    print(f"  💾 Saved initial state: {initial_path}")
    initial_path = Path(initial_path)
    
    # ========================================================================
    # PHASE 2: IMPORT AND EXPERIMENT  
    # ========================================================================
    
    print("\n🎯 Importing RO-Crate and Running Experiment")
    print("=" * 40)
    
    # Import the RO-Crate we just exported
    print("\n🔹 Importing RO-Crate from exported files")
    print(f"  📁 Loading RO-Crate from: {initial_path}")
    
    imported_facade = SchemaFacade.from_ro_crate(initial_path)
    
    print(f"  ✅ Successfully imported RO-Crate!")
    print(f"  📊 Imported {len(imported_facade.types)} types")
    print(f"  📦 Imported {len(imported_facade.metadata_entries)} metadata entries")
    
    # Show what was imported
    print("\n  📋 Imported types:")
    for imported_type in imported_facade.types:
        props = len(imported_type.rdfs_property or [])
        restrictions = len(imported_type.get_restrictions())
        print(f"    - {imported_type.id}: {props} properties, {restrictions} restrictions")
    
    print("\n  📦 Imported metadata entries (first 5):")
    for entry in imported_facade.metadata_entries[:5]:
        print(f"    - {entry.id} (type: {entry.class_id})")
    
    # Import Molecule and Equipment Models
    MoleculeModel = imported_facade.export_pydantic_model("Molecule")
    EquipmentModel = imported_facade.export_pydantic_model("Equipment")
        
    # Know we need molecules: benzene, toluene, aniline
    # And equipment: reactor
    benzene = imported_facade.get_entry_as("benzene", MoleculeModel)
    toluene = imported_facade.get_entry_as("toluene", MoleculeModel)
    aniline = imported_facade.get_entry_as("aniline", MoleculeModel)
    reactor = imported_facade.get_entry_as("reactor", EquipmentModel)
    
    print(f"  ✅ Selected from imported data: {benzene.name}, {toluene.name}, {aniline.name}, {reactor.name}")
    
    # Run experiment
    product_dict, observations_csv = experiment(benzene, toluene, aniline, reactor)

    # Create new product molecule instance
    product = MoleculeModel(**product_dict)

    print(f"  🧪 Experiment complete, product created: {product.name}")
    
    # ========================================================================
    # PHASE 3: UPDATE AND RE-EXPORT
    # ========================================================================
    
    print("\n🎯 Updating Schema with Experimental Results")
    print("=" * 40)
    
    # Create new facade with updated data
    updated_facade = SchemaFacade()
    updated_facade.add_all_registered_models()
    
    # Add all original instances (now with modifications)
    for instance_id, instance in instances.items():
        updated_facade.add_model_instance(instance, instance_id)
    
    # Add new product
    updated_facade.add_model_instance(product, "synthesis_product")
    
    print(f"  📊 Updated schema: {len(updated_facade.types)} types")
    print(f"  📦 Updated entries: {len(updated_facade.metadata_entries)} metadata entries")
    
    # Generate updated RDF
    updated_rdf_graph = updated_facade.to_graph()
    print(f"  🕸️  Updated RDF graph: {len(updated_rdf_graph)} triples")
    print(f"  📈 RDF growth: +{len(updated_rdf_graph) - len(rdf_graph)} triples")
    
    # Export final state
    print("\n🔹 Exporting Final RO-Crate")
    # Add experimental observations file to facade
    updated_facade.add_file(
        file_path=observations_csv,
        name="Experimental Observations",
        description="Detailed measurements from chemical synthesis experiment including temperature, pressure, yields and purity data"
    )
    
    final_path = os.path.join(output_dir, "full_example_final")
    updated_facade.write(
        destination=final_path,
        name="Complex Scientific Workflow - Final State", 
        description="Final RO-Crate after experimental synthesis with observation data",
        license="MIT"
    )
    print(f"  💾 Saved final state: {final_path}")
    final_path = Path(final_path)
    
    # ========================================================================
    # PHASE 4: ANALYSIS
    # ========================================================================
    
    print("\n🎯 WORKFLOW ANALYSIS & RESULTS")
    print("=" * 40)
    
    # Compare facades (original vs imported)
    print("\n🔹 Import Fidelity Analysis")
    print(f"  📊 Original facade: {len(facade.types)} types, {len(facade.metadata_entries)} entries")
    print(f"  📊 Imported facade: {len(imported_facade.types)} types, {len(imported_facade.metadata_entries)} entries")
    
    # Check if all types were preserved
    original_type_ids = {t.id for t in facade.types}
    imported_type_ids = {t.id for t in imported_facade.types}
    if original_type_ids == imported_type_ids:
        print(f"  ✅ All {len(original_type_ids)} types preserved in import")
    else:
        print(f"  ⚠️  Type mismatch: original={len(original_type_ids)}, imported={len(imported_type_ids)}")
        missing_types = original_type_ids - imported_type_ids
        if missing_types:
            print(f"     Missing: {missing_types}")
        extra_types = imported_type_ids - original_type_ids  
        if extra_types:
            print(f"     Extra: {extra_types}")
    
    # Check if all metadata entries were preserved
    original_entry_ids = {e.id for e in facade.metadata_entries}
    imported_entry_ids = {e.id for e in imported_facade.metadata_entries}
    if original_entry_ids == imported_entry_ids:
        print(f"  ✅ All {len(original_entry_ids)} metadata entries preserved in import")
    else:
        print(f"  ⚠️  Metadata entry mismatch: original={len(original_entry_ids)}, imported={len(imported_entry_ids)}")
        missing_entries = original_entry_ids - imported_entry_ids
        if missing_entries:
            print(f"     Missing: {missing_entries}")
        extra_entries = imported_entry_ids - original_entry_ids
        if extra_entries:
            print(f"     Extra: {extra_entries}")
    
    # Compare files
    analyze_rocrate_changes(initial_path, final_path)
    
    # Show experimental modifications
    print("\n🔹 Experimental Modifications Detected")
    print(f"  🧪 New molecule created: {product.name}")
    print(f"     SMILES: {product.smiles}")
    print(f"     Notes: {product.experimental_notes}")
    
    print(f"\n  📝 Modified molecules:")
    modified_molecules = [instances['benzene'], instances['toluene']]
    for mol in modified_molecules:
        if mol.experimental_notes:
            print(f"     - {mol.name}: {mol.experimental_notes}")
    
    # Summary statistics
    print("\n🔹 Final Statistics")
    print(f"  📊 Original facade: {len(facade.types)} types, {len(facade.metadata_entries)} entries")
    print(f"  📊 Imported facade: {len(imported_facade.types)} types, {len(imported_facade.metadata_entries)} entries")
    print(f"  � Final facade: {len(updated_facade.types)} types, {len(updated_facade.metadata_entries)} entries")
    print(f"  🕸️  Final RDF triples: {len(updated_rdf_graph)}")
    print(f"  🔄 Round-trip cycles: 3 (export → import → experiment → export)")
    print(f"  ⚗️  Experiments performed: 1")
    print(f"  🆕 New entities created: 1")
    print(f"  ✏️  Entities modified: 2")
    
    print("\n" + "="*80)
    print("🎉 COMPREHENSIVE WORKFLOW WITH IMPORT DEMONSTRATION COMPLETE!")
    print("   📁 RO-Crates created:")
    print(f"      - Initial: {initial_path}")
    print(f"      - Final: {final_path}")
    print("="*80)
    
    return {
        'initial_facade': facade,
        'imported_facade': imported_facade,
        'updated_facade': updated_facade,
        'instances': instances,
        'product': product,
        'initial_path': initial_path,
        'final_path': final_path
    }


if __name__ == "__main__":
    results = main()