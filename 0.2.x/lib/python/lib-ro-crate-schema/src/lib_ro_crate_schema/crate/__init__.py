"""
RO-Crate interoperability profile implementation.
"""

__version__ = "0.2.0"

# Core schema components
from .schema_facade import SchemaFacade
from .type import Type
from .type_property import TypeProperty
from .metadata_entry import MetadataEntry
from .restriction import Restriction

# Schema registry and decorator system  
from .schema_registry import SchemaRegistry, TypeTemplate, TypePropertyTemplate, get_schema_registry
from .decorators import ro_crate_schema, Field, register_model, is_ro_crate_model, get_registered_models

__all__ = [
    # Version
    "__version__",
    
    # Core components
    "SchemaFacade",
    "Type", 
    "TypeProperty",
    "MetadataEntry",
    "Restriction",
    
    # Registry system
    "SchemaRegistry",
    "TypeTemplate", 
    "TypePropertyTemplate",
    "get_schema_registry",
    
    # Decorator API
    "ro_crate_schema",
    "Field",
    "register_model",
    "is_ro_crate_model", 
    "get_registered_models",
]