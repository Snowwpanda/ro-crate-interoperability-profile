"""
Minimal example showing basic Pydantic model usage with RO-Crate schema decorators.
This demonstrates the simplest way to create an RO-Crate with typed entities.
"""

from pydantic import BaseModel
from lib_ro_crate_schema.crate.decorators import ro_crate_schema, Field
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.jsonld_utils import add_schema_to_crate
from rocrate.rocrate import ROCrate
from pathlib import Path


# Define a simple Person schema
@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    """Person entity in the RO-Crate"""
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    email: str = Field(json_schema_extra={"ontology": "https://schema.org/email"})


def main():
    """Minimal example: Create a Person and export to RO-Crate"""
    
    print("Creating a Person instance...")
    person = Person(name="Alice Researcher", email="alice@example.org")
    
    print("Building RO-Crate...")
    # Create schema facade and add registered models
    facade = SchemaFacade()
    facade.add_all_registered_models()
    
    # Add the person instance
    facade.add_model_instance(person, "alice")
    
    # Create RO-Crate
    crate = ROCrate()
    crate.name = "Minimal Example"
    crate.description = "A minimal RO-Crate with one Person"
    
    final_crate = add_schema_to_crate(facade, crate)
    
    # Export
    output_path = Path("output_crates/minimal_example")
    output_path.mkdir(parents=True, exist_ok=True)
    final_crate.write(output_path)
    
    print(f"✓ RO-Crate exported to: {output_path}")
    print(f"✓ Entities: {len(final_crate.get_entities())}")


if __name__ == "__main__":
    main()
