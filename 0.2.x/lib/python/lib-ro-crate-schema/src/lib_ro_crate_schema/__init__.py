"""
RO-Crate Schema Library
========================

A Pythonic library for creating and managing RO-Crates with schema definitions using Pydantic models.

Quick Start
-----------

.. code-block:: python

    from lib_ro_crate_schema import SchemaFacade, ro_crate_schema, Field
    from pydantic import BaseModel
    
    @ro_crate_schema(ontology="https://schema.org/Person")
    class Person(BaseModel):
        name: str = Field(ontology="https://schema.org/name")
        email: str = Field(ontology="https://schema.org/email")
    
    # Create and export
    facade = SchemaFacade()
    facade.add_all_registered_models()
    person = Person(name="Alice", email="alice@example.com")
    facade.add_model_instance(person, "person_001")
    facade.write("my_crate")

"""

__version__ = "0.2.0"

# Import core components from crate module
from .crate import (
    # Core components
    SchemaFacade,
    Type,
    TypeProperty,
    MetadataEntry,
    Restriction,
    
    # Decorator API (recommended for most users)
    ro_crate_schema,
    Field,
    
    # Registry system (advanced usage)
    SchemaRegistry,
    get_schema_registry,
    register_model,
    is_ro_crate_model,
    get_registered_models,
)

__all__ = [
    # Version
    "__version__",
    
    # Core components
    "SchemaFacade",
    "Type",
    "TypeProperty",
    "MetadataEntry",
    "Restriction",
    
    # Decorator API (most commonly used)
    "ro_crate_schema",
    "Field",
    
    # Registry system
    "SchemaRegistry",
    "get_schema_registry",
    "register_model",
    "is_ro_crate_model",
    "get_registered_models",
]
