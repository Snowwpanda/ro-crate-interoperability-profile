"""
Test RO-Crate export functionality.
Verifies that Pydantic models can be converted to RO-Crate format.
"""

import json
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field
from lib_ro_crate_schema.crate.decorators import ro_crate_schema
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.jsonld_utils import add_schema_to_crate
from rocrate.rocrate import ROCrate


@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    """Person entity"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    email: str = Field(json_schema_extra={"ontology": "https://schema.org/email"})


@ro_crate_schema(ontology="https://schema.org/Dataset")
class Dataset(BaseModel):
    """Dataset entity"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    description: str = Field(json_schema_extra={"ontology": "https://schema.org/description"})


def test_basic_export():
    """Test that we can export Pydantic models to RO-Crate"""
    
    # Create instances
    person = Person(name="Test Person", email="test@example.org")
    dataset = Dataset(name="Test Dataset", description="Test description")
    
    # Create facade
    facade = SchemaFacade()
    facade.add_all_registered_models()
    facade.add_model_instance(person, "test_person")
    facade.add_model_instance(dataset, "test_dataset")
    
    # Export to RO-Crate
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_crate"
        
        crate = ROCrate()
        crate.name = "Test Crate"
        final_crate = add_schema_to_crate(facade, crate)
        final_crate.write(output_path)
        
        # Verify output
        metadata_file = output_path / "ro-crate-metadata.json"
        assert metadata_file.exists(), "Metadata file not created"
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        assert "@context" in metadata
        assert "@graph" in metadata
        assert len(metadata["@graph"]) > 0
        
        print("✓ Export test passed")


def test_json_ld_structure():
    """Test that exported RO-Crate has valid JSON-LD structure"""
    
    person = Person(name="Alice", email="alice@example.org")
    
    facade = SchemaFacade()
    facade.add_all_registered_models()
    facade.add_model_instance(person, "alice")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_crate"
        
        crate = ROCrate()
        final_crate = add_schema_to_crate(facade, crate)
        final_crate.write(output_path)
        
        with open(output_path / "ro-crate-metadata.json") as f:
            metadata = json.load(f)
        
        # Check JSON-LD structure
        assert isinstance(metadata["@context"], (str, list, dict))
        assert isinstance(metadata["@graph"], list)
        
        # Check for entity types
        types = set()
        for entity in metadata["@graph"]:
            entity_type = entity.get("@type")
            if isinstance(entity_type, list):
                types.update(entity_type)
            elif entity_type:
                types.add(entity_type)
        
        assert "Person" in types or any("Person" in t for t in types)
        
        print("✓ JSON-LD structure test passed")


if __name__ == "__main__":
    test_basic_export()
    test_json_ld_structure()
    print("\n✅ All export tests passed!")
