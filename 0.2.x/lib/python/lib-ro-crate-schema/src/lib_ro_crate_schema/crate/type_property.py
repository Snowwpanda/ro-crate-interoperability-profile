"""
TypeProperty class for RO-Crate schema representation.
Represents RDFS Properties that define relationships between entities.
"""
from __future__ import annotations

from typing import List, Optional, Union, Generator, TYPE_CHECKING, Any
from pydantic import BaseModel, Field
from lib_ro_crate_schema.crate.rdf import is_type, object_id
from lib_ro_crate_schema.crate.forward_ref_resolver import ForwardRefResolver
from lib_ro_crate_schema.crate.literal_type import LiteralType
from rdflib import RDF, RDFS, Literal, URIRef
from urllib.parse import urlparse

if TYPE_CHECKING:
    from .type import Type


class TypeProperty(BaseModel):
    """
    Represents an RDFS Property in the RO-Crate schema (equivalent to Java IPropertyType interface).
    Defines relationships and attributes that can exist between entities in the knowledge graph.
    
    Key Responsibilities:
    - Define RDFS Property metadata (ID, label, comment, domain/range)
    - Specify allowed domains (which classes can have this property)
    - Specify allowed ranges (what values/types this property can hold)
    - Generate OWL cardinality constraints (required/optional, single/multiple values)
    - Support ontological alignment via equivalent properties
    
    Commonly Used Methods:
    
    **Fluent Builder API:**
    - setId(id) -> Set the RDFS Property identifier
    - setLabel(label) -> Set human-readable label (rdfs:label)
    - setComment(comment) -> Set description (rdfs:comment)
    - setTypes(types) -> Set allowed value types (schema:rangeIncludes)
    - addType(type_ref) -> Add single allowed value type
    - setRequired(required) -> Set if property is mandatory (affects cardinality)
    - setOntologicalAnnotations(annotations) -> Set owl:equivalentProperty mappings
    
    **Java API Compatibility (IPropertyType):**
    - getId() -> Get the RDFS Property identifier
    - getLabel() -> Get human-readable label
    - getComment() -> Get description text
    - getDomain() -> Get allowed domain classes (schema:domainIncludes)
    - getRange() -> Get allowed value types (schema:rangeIncludes)
    - getOntologicalAnnotations() -> Get equivalent property mappings
    - get_min_cardinality() -> Get minimum required values (0=optional, 1=required)
    - get_max_cardinality() -> Get maximum allowed values (1=single, 0=unlimited)
    
    **RDF Generation:**
    - to_triples() -> Generate RDF triples for serialization
    - resolve(registry) -> Resolve forward references to other objects
    
    Usage Example:
        name_prop = TypeProperty(id="name")
        name_prop.setLabel("Name").setComment("Person's full name")
        name_prop.setTypes(["xsd:string"]).setRequired(True)
        
    JSON-LD Output Example:
        {
            "@id": "name",
            "@type": "rdf:Property",
            "rdfs:label": "Name", 
            "rdfs:comment": "Person's full name",
            "schema:domainIncludes": {"@id": "Person"},
            "schema:rangeIncludes": {"@id": "http://www.w3.org/2001/XMLSchema#string"},
            "owl:equivalentProperty": {"@id": "https://schema.org/name"}
        }
        
        Related OWL Restriction (when used on a class):
        {
            "@id": "Person_name_restriction",
            "@type": "owl:Restriction",
            "owl:onProperty": {"@id": "name"},
            "owl:minCardinality": 1,
            "owl:maxCardinality": 1
        }
    """
    id: str
    domain_includes: List[str] = Field(default_factory=list)
    range_includes: List[Union[str, LiteralType, Any]] = Field(default_factory=list) 
    ontological_annotations: Optional[List[str]] = Field(default=None)
    comment: Optional[str] = Field(default=None)
    label: Optional[str] = Field(default=None)
    required: Optional[bool] = Field(default=None, description="Whether this property is required (generates OWL restrictions)")
    
    # Fluent builder API methods
    def setId(self, id: str):
        """Set the ID of this property"""
        self.id = id
        return self
        
    def setTypes(self, types: List[Union[str, Type]]):
        """Set the range types for this property"""
        self.range_includes = []
        for type_ref in types:
            if hasattr(type_ref, 'id'):
                self.range_includes.append(type_ref.id)
            else:
                # Preserve enum objects as-is, convert only plain strings
                self.range_includes.append(type_ref)
        return self
        
    def addType(self, type_ref: Union[str, Type]):
        """Add a single type to the range of this property"""
        if hasattr(type_ref, 'id'):
            self.range_includes.append(type_ref.id)
        else:
            # Preserve enum objects as-is, convert only plain strings
            self.range_includes.append(type_ref)
        return self
        
    def setOntologicalAnnotations(self, annotations: List[str]):
        """Set ontological annotations for this property"""
        self.ontological_annotations = annotations
        return self
        
    def setRequired(self, required: bool):
        """Set whether this property is required (generates OWL restrictions)"""
        self.required = required
        return self
        
    def setComment(self, comment: str):
        """Set the comment for this property"""
        self.comment = comment
        return self
        
    def setLabel(self, label: str):
        """Set the label for this property"""
        self.label = label
        return self
    
    # Java API compatibility getter methods
    def get_min_cardinality(self) -> int:
        """Get minimum cardinality for this property (0 = optional, 1 = required)"""
        if self.required is True:
            return 1
        elif self.required is False:
            return 0
        else:
            return 0  # Default to optional if not explicitly set
    
    def get_max_cardinality(self) -> int:
        """Get maximum cardinality for this property (0 = unbounded, 1 = single value)"""
        # For now, assume single values unless explicitly configured
        # This could be enhanced to detect list types in range_includes
        return 1

    # Java API compatibility getter methods
    def getId(self) -> str:
        """Get the RDFS Property identifier (Java IPropertyType interface)"""
        return self.id
    
    def getLabel(self) -> Optional[str]:
        """Get human-readable label (Java IPropertyType interface)"""
        return self.label
    
    def getComment(self) -> Optional[str]:
        """Get description text (Java IPropertyType interface)"""
        return self.comment
    
    def getDomain(self) -> List[str]:
        """Get allowed domain classes (Java IPropertyType interface)"""
        return self.domain_includes
    
    def getRange(self) -> List[Union[str, LiteralType, Any]]:
        """Get allowed value types (Java IPropertyType interface)"""
        return self.range_includes
    
    def getOntologicalAnnotations(self) -> List[str]:
        """Get equivalent property mappings (Java IPropertyType interface)"""
        return self.ontological_annotations or []
    
    def resolve(self, registry: ForwardRefResolver):
        """Resolve forward references using the registry"""
        # For now, TypeProperty doesn't have complex forward refs to resolve
        pass

    def to_triples(self) -> Generator[tuple, None, None]:
        """
        Emits the property definition as a set of triples
        whose subject is a RDFS:Property
        """
        yield is_type(self.id, RDF.Property)
        
        if self.label:
            yield (object_id(self.id), RDFS.label, Literal(self.label))
            
        if self.comment:
            yield (object_id(self.id), RDFS.comment, Literal(self.comment))
        
        # Domain includes - what types can have this property
        for domain in self.domain_includes:
            yield (object_id(self.id), URIRef("https://schema.org/domainIncludes"), object_id(domain))
        
        # Range includes - what types can be values of this property  
        for range_val in self.range_includes:
            # Convert enum to string value if needed
            if isinstance(range_val, LiteralType):
                range_str = range_val.value
            else:
                range_str = str(range_val)
                
            if range_str.startswith("xsd:"):
                # XSD type
                xsd_uri = range_str.replace("xsd:", "http://www.w3.org/2001/XMLSchema#")
                yield (object_id(self.id), URIRef("https://schema.org/rangeIncludes"), URIRef(xsd_uri))
            elif range_str.startswith("base:"):
                # Reference to another type in our schema
                type_id = range_str.replace("base:", "")
                yield (object_id(self.id), URIRef("https://schema.org/rangeIncludes"), object_id(type_id))
            else:
                # Assume it's a full URI or local reference
                yield (object_id(self.id), URIRef("https://schema.org/rangeIncludes"), object_id(range_str))
        
        # Ontological annotations
        if self.ontological_annotations:
            for annotation in self.ontological_annotations:
                yield (object_id(self.id), URIRef("http://www.w3.org/2002/07/owl#equivalentProperty"), URIRef(annotation))
