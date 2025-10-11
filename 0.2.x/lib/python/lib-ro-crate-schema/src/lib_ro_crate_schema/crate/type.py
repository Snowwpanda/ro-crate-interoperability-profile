from typing import List, Generator, Union, Optional

from lib_ro_crate_schema.crate.rdf import is_type, object_id
from lib_ro_crate_schema.crate.forward_ref_resolver import ForwardRef, ForwardRefResolver
from .restriction import Restriction
from .type_property import TypeProperty
from pydantic import BaseModel, Field
from rdflib import Node, Literal, URIRef, RDFS, OWL


class Type(BaseModel):
    """
    Represents an RDFS Class in the RO-Crate schema (equivalent to Java IType interface).
    Defines the structure and constraints for entities in the knowledge graph.
    
    Key Responsibilities:
    - Define RDFS Class metadata (ID, label, comment, inheritance)
    - Associate TypeProperty objects that define allowed properties
    - Generate OWL restrictions for property cardinality constraints
    - Support ontological alignment via equivalent classes
    
    Commonly Used Methods:
    
    **Fluent Builder API:**
    - setId(id) -> Set the RDFS Class identifier
    - setLabel(label) -> Set human-readable label (rdfs:label)
    - setComment(comment) -> Set description (rdfs:comment)
    - addProperty(property) -> Add allowed TypeProperty
    - setOntologicalAnnotations(annotations) -> Set owl:equivalentClass mappings
    
    **Java API Compatibility (IType):**
    - getId() -> Get the RDFS Class identifier
    - getLabel() -> Get human-readable label
    - getComment() -> Get description text
    - getSubClassOf() -> Get parent class inheritance
    - getOntologicalAnnotations() -> Get equivalent class mappings
    - get_restrictions() -> Get OWL cardinality restrictions
    
    **RDF Generation:**
    - to_triples() -> Generate RDF triples for serialization
    - resolve(registry) -> Resolve forward references to other objects
    
    Usage Example:
        person_type = Type(id="Person")
        person_type.setLabel("Person").setComment("Represents a person")
        person_type.addProperty(name_property)
        person_type.addProperty(email_property)
        
    JSON-LD Output Example:
        {
            "@id": "Person",
            "@type": "rdfs:Class",
            "rdfs:label": "Person",
            "rdfs:comment": "Represents a person in the system",
            "rdfs:subClassOf": {"@id": "https://schema.org/Thing"},
            "owl:equivalentClass": {"@id": "https://schema.org/Person"},
            "owl:restriction": [
                {
                    "@id": "Person_name_restriction"
                },
                {
                    "@id": "Person_email_restriction"
                }
            ]
        }
    """
    id: str
    subclass_of: List[Union[str, "Type", ForwardRef]] = Field(default_factory=lambda: ["https://schema.org/Thing"])
    ontological_annotations: Optional[List[str]] = Field(default=None)
    rdfs_property: Optional[List[TypeProperty]] = Field(default_factory=list)
    comment: Optional[str] = Field(default=None)
    label: Optional[str] = Field(default=None)
    restrictions: Optional[List[Restriction]] = Field(default=None)
    
    # Fluent builder API methods
    def setId(self, id: str):
        """Set the ID of this type"""
        self.id = id
        return self
    
    def setOntologicalAnnotations(self, annotations: List[str]):
        """Set ontological annotations"""
        self.ontological_annotations = annotations
        return self
        
    def addProperty(self, property: TypeProperty):
        """Add a property to this type"""
        if self.rdfs_property is None:
            self.rdfs_property = []
        self.rdfs_property.append(property)
        return self
        
    def setComment(self, comment: str):
        """Set the comment for this type"""
        self.comment = comment
        return self
        
    def setLabel(self, label: str):
        """Set the label for this type"""
        self.label = label
        return self

    def get_restrictions(self) -> List[Restriction]:
        """
        Get the restrictions that represent the properties of this type (RDFS:Class).
        Returns restrictions that define cardinality constraints for properties.
        Auto-generates restrictions from properties with explicit required/optional specification.
        """
        restrictions = list(self.restrictions or [])
        
        # Auto-generate restrictions from properties with required field set
        if self.rdfs_property:
            for prop in self.rdfs_property:
                # Check if a restriction already exists for this property
                if any(r.property_type == prop.id for r in restrictions):
                    continue  # Skip if restriction already defined
                min_cardinality = 1 if prop.required is not None and prop.required else 0
                # Generate restriction ID based on type and property
                restriction_id = f"{self.id}_{prop.id}_restriction"
                
                # Create restriction for this property
                restriction = Restriction(
                    id=restriction_id,
                    property_type=prop.id,
                    min_cardinality=min_cardinality
                )
                restrictions.append(restriction)
        
        return restrictions
    
    # Java API compatibility getter methods
    def getId(self) -> str:
        """Get the RDFS Class identifier (Java IType interface)"""
        return self.id
    
    def getLabel(self) -> Optional[str]:
        """Get human-readable label (Java IType interface)"""
        return self.label
    
    def getComment(self) -> Optional[str]:
        """Get description text (Java IType interface)"""
        return self.comment
    
    def getSubClassOf(self) -> List[str]:
        """Get parent class inheritance (Java IType interface)"""
        result = []
        for parent in self.subclass_of or []:
            if isinstance(parent, str):
                result.append(parent)
            elif hasattr(parent, 'id'):
                result.append(parent.id)
            else:
                result.append(str(parent))
        return result
    
    def getOntologicalAnnotations(self) -> List[str]:
        """Get equivalent class mappings (Java IType interface)"""
        return self.ontological_annotations or []

    def resolve(self, registry: ForwardRefResolver):
        """Resolve forward references using the registry"""
        if self.rdfs_property:
            for prop in self.rdfs_property:
                if hasattr(prop, 'resolve'):
                    prop.resolve(registry)

    def to_triples(self) -> Generator[tuple, None, None]:
        """
        Emits the type definition as a set of triples
        whose subject is a RDFS:Class
        """
        yield is_type(self.id, RDFS.Class)
        
        if self.comment:
            yield (object_id(self.id), RDFS.comment, Literal(self.comment))
        
        if self.label:
            yield (object_id(self.id), RDFS.label, Literal(self.label))
        
        # Subclass relationships
        if self.subclass_of:
            for parent in self.subclass_of:
                parent_id = parent if isinstance(parent, str) else parent.id
                yield (object_id(self.id), RDFS.subClassOf, URIRef(parent_id))
        
        # Ontological annotations
        if self.ontological_annotations:
            for annotation in self.ontological_annotations:
                yield (object_id(self.id), OWL.equivalentClass, URIRef(annotation))
        
        # OWL Restrictions (cardinality constraints on properties)
        restrictions = self.get_restrictions()
        if restrictions:
            # Generate all restriction triples and link them to this class
            for restriction in restrictions:
                # Generate the full restriction triples (type, onProperty, cardinality)
                yield from restriction.to_triples()
                # Link this restriction to the class via owl:restriction property
                owl_restriction_property = URIRef("http://www.w3.org/2002/07/owl#restriction")
                yield (object_id(self.id), owl_restriction_property, object_id(restriction.id))
        
        # Properties (with domain set to this type)
        if self.rdfs_property:
            for prop in self.rdfs_property:
                prop_with_domain = prop.model_copy(update=dict(domain_includes=[self.id]))
                yield from prop_with_domain.to_triples()


# Rebuild the model to handle forward references
Type.model_rebuild()
