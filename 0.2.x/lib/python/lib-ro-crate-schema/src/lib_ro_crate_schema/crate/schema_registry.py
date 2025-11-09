"""
Schema registry for managing Pydantic model registration and metadata extraction.
"""
from typing import Dict, Type, List, Any, Optional, get_type_hints, get_origin, get_args
from dataclasses import dataclass
from pydantic import BaseModel
import datetime
from decimal import Decimal


@dataclass
class TypePropertyTemplate:
    """Template for creating TypeProperty objects from Pydantic model fields"""
    name: str
    python_type: Type
    rdf_type: str
    required: bool
    is_list: bool
    ontology: Optional[str] = None
    comment: Optional[str] = None
    default_value: Any = None


@dataclass 
class TypeTemplate:
    """
    Template for creating Type objects from @ro_crate_schema decorated Pydantic models.
    
    The 'id' field stores the RO-Crate schema identifier, which may be different from the
    Python class name if explicitly set via @ro_crate_schema(id="...").
    """
    id: str  # RO-Crate schema identifier (may differ from Python class name)
    model_class: Type[BaseModel]
    ontology: Optional[str] = None
    comment: Optional[str] = None
    type_properties: List[TypePropertyTemplate] = None
    
    def __post_init__(self):
        if self.type_properties is None:
            self.type_properties = []


class SchemaRegistry:
    """
    Global registry for @ro_crate_schema decorated Pydantic models.
    
    This registry stores TypeTemplates (will become Type objects) and TypePropertyTemplates
    (will become TypeProperty objects). It does NOT store MetadataEntry objects - those
    are created separately in SchemaFacade from Pydantic model instances.
    
    Purpose: Bridge between Pydantic models and RO-Crate schema objects
    """
    
    def __init__(self):
        self._registered_types: Dict[str, TypeTemplate] = {}
        self._type_converter = TypeConverter()
    
    def register_type_from_model(self, model_class: Type[BaseModel], type_id: str, 
                                 ontology: Optional[str] = None, 
                                 comment: Optional[str] = None) -> TypeTemplate:
        """Register a Pydantic model and extract template for Type creation"""
        
        # Extract type properties from Pydantic model fields
        type_properties = self._extract_type_properties(model_class)
        
        type_template = TypeTemplate(
            id=type_id,  # Use explicit type_id instead of class name
            model_class=model_class,
            ontology=ontology,
            comment=comment or model_class.__doc__,
            type_properties=type_properties
        )
        
        # Store by the type_id, not class name
        self._registered_types[type_id] = type_template
        return type_template
    
    def get_type_template(self, type_id: str) -> Optional[TypeTemplate]:
        """Get type template for a registered @ro_crate_schema model by id"""
        return self._registered_types.get(type_id)
    
    def get_all_type_templates(self) -> Dict[str, TypeTemplate]:
        """Get all registered type templates from @ro_crate_schema models"""
        return self._registered_types.copy()
    
    def is_type_registered(self, type_id: str) -> bool:
        """Check if a @ro_crate_schema decorated model is registered"""
        return type_id in self._registered_types
        
    def _extract_type_properties(self, model_class: Type[BaseModel]) -> List[TypePropertyTemplate]:
        """Extract TypeProperty templates from Pydantic model fields"""
        type_property_templates = []
        
        for field_name, field_info in model_class.model_fields.items():
            # Get the field type
            field_type = field_info.annotation
            
            # Check if it's a list/optional type
            is_list = self._is_list_type(field_type)
            if is_list:
                # Extract the inner type for lists
                field_type = get_args(field_type)[0] if get_args(field_type) else field_type
            
            # Convert to RDF type
            rdf_type = self._type_converter.python_to_rdf(field_type)
            
            # Extract ontology and comment annotations from field metadata
            json_extra = getattr(field_info, 'json_schema_extra', None) if hasattr(field_info, 'json_schema_extra') else None
            ontology = json_extra.get('ontology') if json_extra else None
            # Prefer comment from json_schema_extra, fallback to description
            comment = json_extra.get('comment') if json_extra else None
            if comment is None:
                comment = field_info.description
            
            type_property_template = TypePropertyTemplate(
                name=field_name,
                python_type=field_type,
                rdf_type=rdf_type,
                required=field_info.is_required(),
                is_list=is_list,
                ontology=ontology,
                comment=comment,
                default_value=field_info.default if field_info.default is not ... else None
            )
            
            type_property_templates.append(type_property_template)
        
        return type_property_templates
    
    def _is_list_type(self, type_annotation) -> bool:
        """Check if a type annotation represents a list"""
        origin = get_origin(type_annotation)
        return origin is list or origin is List


class TypeConverter:
    """Converts Python types to XSD/RDF types"""
    
    # Mapping from Python types to XSD types
    TYPE_MAPPING = {
        str: "xsd:string",
        int: "xsd:integer",
        float: "xsd:float", 
        bool: "xsd:boolean",
        datetime.datetime: "xsd:dateTime",
        datetime.date: "xsd:date",
        datetime.time: "xsd:time",
        Decimal: "xsd:decimal",
        bytes: "xsd:base64Binary",
    }
    
    def python_to_rdf(self, python_type: Type) -> str:
        """Convert a Python type to its corresponding XSD/RDF type"""
        # Handle Union types (Optional, etc.)
        if hasattr(python_type, '__origin__'):
            origin = get_origin(python_type)
            if origin is type(None):  # Handle NoneType
                return "xsd:string"  # Default fallback
            elif hasattr(python_type, '__args__'):
                # For Union types, take the first non-None type
                args = get_args(python_type)
                for arg in args:
                    if arg is not type(None):
                        return self.python_to_rdf(arg)
        
        # Handle Pydantic models (reference types)
        if isinstance(python_type, type) and issubclass(python_type, BaseModel):
            return f"base:{python_type.__name__}"  # Reference to another model
            
        # Look up in type mapping
        return self.TYPE_MAPPING.get(python_type, "xsd:string")
    
    def add_type_mapping(self, python_type: Type, rdf_type: str):
        """Add a custom type mapping"""
        self.TYPE_MAPPING[python_type] = rdf_type


# Global decorator registry instance
_schema_registry = SchemaRegistry()


def get_schema_registry() -> SchemaRegistry:
    """
    Get the global schema registry for @ro_crate_schema decorated Pydantic models.
    
    This registry contains TypeTemplates that can be converted to Type objects
    and TypePropertyTemplates that can be converted to TypeProperty objects.
    MetadataEntry objects are NOT stored here - they're created in SchemaFacade.
    """
    return _schema_registry