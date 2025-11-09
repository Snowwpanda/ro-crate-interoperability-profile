"""
Decorator system for registering Pydantic models as RO-Crate schema types.
"""
from typing import Type, Optional, Any, Union
from functools import wraps
from pydantic import BaseModel, Field as PydanticField

from .schema_registry import get_schema_registry, TypeTemplate


def Field(ontology: Optional[str] = None, comment: Optional[str] = None, **kwargs):
    """Enhanced Pydantic Field that supports ontology annotations for RO-Crate schema generation.
    
    Args:
        ontology: URI of the ontological concept this field represents (deprecated: use json_schema_extra)
        comment: Human-readable description of this field (deprecated: use json_schema_extra)
        **kwargs: Standard Pydantic Field arguments, including json_schema_extra
    
    Returns:
        Pydantic FieldInfo with RO-Crate metadata
    
    Example (recommended):
        name: str = Field(json_schema_extra={"ontology": "https://schema.org/name", "comment": "Person's full name"})
    
    Example (deprecated but still supported):
        name: str = Field(ontology="https://schema.org/name", comment="Person's full name")
    """
    # Store RO-Crate specific metadata in json_schema_extra
    json_schema_extra = kwargs.get('json_schema_extra', {})
    if ontology is not None:
        json_schema_extra['ontology'] = ontology
    if comment is not None:
        json_schema_extra['comment'] = comment
    
    if json_schema_extra:  # Only set if we have RO-Crate metadata
        kwargs['json_schema_extra'] = json_schema_extra
    
    # Set description from comment if not provided and remove any lingering ontology/comment
    if comment is not None and 'description' not in kwargs:
        kwargs['description'] = comment
    
    # Ensure ontology and comment are not passed directly to PydanticField
    # (they should only be in json_schema_extra)
    kwargs.pop('ontology', None)
    kwargs.pop('comment', None)
    
    return PydanticField(**kwargs)


def ro_crate_schema(
    ontology: Optional[str] = None,
    comment: Optional[str] = None,
    auto_register: bool = True,
    id: Optional[str] = None
):
    """Decorator to mark Pydantic models as RO-Crate schema types.
    
    This decorator registers the model in the global schema registry and enables
    automatic schema generation for RO-Crate interoperability.
    
    Args:
        ontology: URI of the ontological concept this model represents
        comment: Human-readable description of this model type
        auto_register: Whether to automatically register the model (default: True)
        id: RO-Crate schema ID for the type (defaults to class name if not provided)
    
    Returns:
        Decorated Pydantic model class with RO-Crate metadata
    
    Example:
        @ro_crate_schema(id="Person", ontology="https://schema.org/Person")
        class PersonModel(BaseModel):
            name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
            email: str = Field(json_schema_extra={"ontology": "https://schema.org/email"})
    """
    def decorator(cls: Type[BaseModel]) -> Type[BaseModel]:
        # Ensure it's a Pydantic model
        if not issubclass(cls, BaseModel):
            raise TypeError(f"@ro_crate_schema can only be applied to Pydantic BaseModel classes, got {cls}")
        
        # Determine the ID to use (explicit id parameter or class name)
        type_id = id if id is not None else cls.__name__
        
        # Store RO-Crate metadata on the class
        cls._ro_crate_ontology = ontology
        cls._ro_crate_comment = comment or cls.__doc__
        cls._ro_crate_registered = auto_register
        cls._ro_crate_id = type_id  # Store the explicit ID
        
        # Auto-register in the global schema registry
        if auto_register:
            registry = get_schema_registry()
            type_template = registry.register_type_from_model(
                model_class=cls,
                type_id=type_id,  # Use the determined ID
                ontology=ontology,
                comment=comment or cls.__doc__
            )
            cls._ro_crate_type_template = type_template
        
        # Add helper methods to the class
        cls.get_ro_crate_metadata = classmethod(_get_ro_crate_metadata)
        cls.to_ro_crate_type = classmethod(_to_ro_crate_type)
        
        return cls
    
    return decorator


def _get_ro_crate_metadata(cls) -> Optional[TypeTemplate]:
    """Get the RO-Crate metadata for this model class."""
    if hasattr(cls, '_ro_crate_type_template'):
        return cls._ro_crate_type_template
    
    # Try to get from registry using the stored ID or class name as fallback
    registry = get_schema_registry()
    if hasattr(cls, '_ro_crate_id'):
        return registry.get_type_template(cls._ro_crate_id)
    else:
        # Fallback to class name for backward compatibility
        return registry.get_type_template(cls.__name__)


def _to_ro_crate_type(cls):
    """Convert this model class to a Type object for RO-Crate schema generation."""
    from .type import Type
    from .type_property import TypeProperty
    from .restriction import Restriction
    
    type_template = cls.get_ro_crate_metadata()
    if not type_template:
        raise ValueError(f"Model {cls.__name__} is not registered with RO-Crate schema")
    
    # Convert properties
    properties = []
    restrictions = []
    
    for prop_template in type_template.type_properties:
        # Create TypeProperty
        type_property = TypeProperty(
            id=prop_template.name,
            range_includes=[prop_template.rdf_type],
            domain_includes=[],  # Will be set by SchemaFacade
            ontological_annotations=[prop_template.ontology] if prop_template.ontology else [],
            comment=prop_template.comment,
            label=prop_template.name.replace('_', ' ').title()
        )
        properties.append(type_property)
        
        # Create restrictions for all fields (required and optional)
        if prop_template.required:
            # Required fields: minCardinality = 1
            restriction = Restriction(
                property_type=prop_template.name,
                min_cardinality=1,
                max_cardinality=1 if not prop_template.is_list else None
            )
        else:
            # Optional fields: minCardinality = 0
            restriction = Restriction(
                property_type=prop_template.name,
                min_cardinality=0,
                max_cardinality=1 if not prop_template.is_list else None
            )
        restrictions.append(restriction)
    
    # Create Type
    ro_crate_type = Type(
        id=type_template.id,  # Use the consistent id field
        subclass_of=["https://schema.org/Thing"],  # Default parent
        ontological_annotations=[type_template.ontology] if type_template.ontology else [],
        rdfs_property=properties,
        comment=type_template.comment,
        label=type_template.id,  # Use id as label (could be made customizable)
        restrictions=restrictions
    )
    
    return ro_crate_type


def register_model(
    model_class: Type[BaseModel], 
    ontology: Optional[str] = None, 
    comment: Optional[str] = None,
    type_id: Optional[str] = None
) -> TypeTemplate:
    """Manually register a Pydantic model for RO-Crate Type generation.
    
    This is an alternative to using the @ro_crate_schema decorator.
    
    Args:
        model_class: The Pydantic model class to register
        ontology: URI of the ontological concept this model represents
        comment: Human-readable description of this model type
        type_id: RO-Crate schema ID for the type (defaults to class name if not provided)
    
    Returns:
        TypeTemplate for creating Type objects from the registered model
    """
    registry = get_schema_registry()
    final_type_id = type_id if type_id is not None else model_class.__name__
    return registry.register_type_from_model(model_class, final_type_id, ontology, comment)


def is_ro_crate_model(model_class: Type[BaseModel]) -> bool:
    """Check if a Pydantic model is registered as an RO-Crate schema type."""
    registry = get_schema_registry()
    return registry.is_type_registered(model_class.__name__)


def get_registered_models():
    """Get all registered RO-Crate schema models."""
    registry = get_schema_registry()
    return registry.get_all_type_templates()