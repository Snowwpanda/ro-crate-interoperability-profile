from pydantic import BaseModel, Field
from lib_ro_crate_schema.crate.rdf import is_type, object_id

try:
    from rdflib import URIRef, RDF, Literal
except ImportError:
    # Fallback for when rdflib is not available
    URIRef = str
    Literal = str


from typing import Union, List, Dict, Optional, Any
from datetime import datetime
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.type import Type


class MetadataEntry(BaseModel):
    """
    Represents an RDF Metadata Entry in an RO-Crate (equivalent to Java IMetadataEntry interface).
    Contains the actual data instances that conform to RDFS Class definitions (Type objects).
    
    Key Responsibilities:
    - Store entity data with unique identifier and class type
    - Hold property values (strings, numbers, booleans, dates)
    - Maintain references to other entities in the knowledge graph
    - Provide Java API compatibility for metadata access
    
    Data Structure:
    - id: Unique identifier for this entity (@id in JSON-LD)
    - class_id: RDFS Class this entity instantiates (@type in JSON-LD)
    - properties: Key-value pairs for simple data (strings, numbers, etc.)
    - references: Key-value pairs for relationships to other entities
    
    Commonly Used Methods:
    
    **Java API Compatibility (IMetadataEntry):**
    - getId() -> Get unique entity identifier
    - getClassId() -> Get RDFS Class type this entity instantiates
    - getValues() -> Get all property values (alias for properties)
    - getReferences() -> Get all entity relationships
    - setId(id_value) -> Set unique entity identifier
    - setClassId(class_id) -> Set RDFS Class type
    - setProperties(properties) -> Set all property values at once
    - setReferences(references) -> Set all entity references at once
    - addProperty(key, value) -> Add single property value
    - addReference(key, reference_id) -> Add single reference to another entity
    - addReferences(key, reference_ids) -> Add multiple references for a property
    
    **Data Access:**
    - properties -> Direct access to simple property values
    - references -> Direct access to entity relationships
    - get_values() -> Alias for properties (Java compatibility)
    
    
    **RDF Generation:**
    - to_triples() -> Generate RDF triples for serialization
    
    Usage Examples:
        # Traditional constructor approach
        person = MetadataEntry(
            id="person1",
            class_id="Person", 
            properties={"name": "Alice Johnson", "age": 30},
            references={"knows": ["person2", "person3"]}
        )
        
        # Java-style fluent API approach
        person = (MetadataEntry(id="temp", class_id="temp")
                  .setId("person1")
                  .setClassId("Person")
                  .addProperty("name", "Alice Johnson")
                  .addProperty("age", 30)
                  .addReference("knows", "person2")
                  .addReference("knows", "person3"))
        
        # Batch operations
        person.setProperties({"name": "Bob Smith", "email": "bob@example.com"})
        person.setReferences({"knows": ["person4", "person5"], "worksFor": ["org1"]})
    
    Java Compatibility Features:
        - All setter methods return self for method chaining (fluent interface)
        - Method names follow Java camelCase conventions
        - Supports builder pattern for object construction
        - Compatible with existing constructor-based initialization
        
    JSON-LD Output Example:
        {
            "@id": "person1",
            "@type": "Person",
            "name": "Alice Johnson",
            "age": 30,
            "knows": [{"@id": "person2"}, {"@id": "person3"}]
        }
    """
    id: str
    class_id: str  # Type ID of this entry  
    properties: Dict[str, Any] = Field(default_factory=dict)  # Property values (matches PropertyType concept)
    references: Dict[str, List[str]] = Field(default_factory=dict)  # References to other entries
    
    # Java API compatibility methods
    def getId(self) -> str:
        """Get unique entity identifier (Java IMetadataEntry interface)"""
        return self.id
    
    def getClassId(self) -> str:
        """Get RDFS Class type this entity instantiates (Java IMetadataEntry interface)"""
        return self.class_id
    
    def getValues(self) -> Dict[str, Any]:
        """Get all property values (Java IMetadataEntry interface)"""
        return self.properties
    
    def getReferences(self) -> Dict[str, List[str]]:
        """Get all entity relationships (Java IMetadataEntry interface)"""
        return self.references
    
    def get_values(self) -> Dict[str, Any]:
        """Get property values (alias for properties field for Java API compatibility)"""
        return self.properties

    # Java-style setter methods for compatibility
    def setId(self, id_value: str) -> 'MetadataEntry':
        """Set unique entity identifier (Java setter style)"""
        self.id = id_value
        return self
    
    def setClassId(self, class_id: str) -> 'MetadataEntry':
        """Set RDFS Class type this entity instantiates (Java setter style)"""
        self.class_id = class_id
        return self
    
    def setProperties(self, properties: Dict[str, Any]) -> 'MetadataEntry':
        """Set all property values (Java setter style)"""
        self.properties = properties
        return self
    
    def setReferences(self, references: Dict[str, List[str]]) -> 'MetadataEntry':
        """Set all entity relationships (Java setter style)"""
        self.references = references
        return self
    
    def addProperty(self, key: str, value: Any) -> 'MetadataEntry':
        """Add a single property value (Java fluent style)"""
        self.properties[key] = value
        return self
    
    def addReference(self, key: str, reference_id: str) -> 'MetadataEntry':
        """Add a single reference to another entity (Java fluent style)"""
        if key not in self.references:
            self.references[key] = []
        self.references[key].append(reference_id)
        return self
    
    def addReferences(self, key: str, reference_ids: List[str]) -> 'MetadataEntry':
        """Add multiple references for a property (Java fluent style)"""
        if key not in self.references:
            self.references[key] = []
        self.references[key].extend(reference_ids)
        return self

    def to_triples(self):
        """Generate RDF triples for this metadata entry"""
        subj = object_id(self.id)
        
        # Type declaration 
        yield is_type(self.id, URIRef(self.class_id))
        
        # Property values 
        for prop_name, prop_value in self.properties.items():
            # Handle datetime objects by converting to ISO string
            if isinstance(prop_value, datetime):
                prop_value = prop_value.isoformat()
            yield (subj, object_id(prop_name), Literal(prop_value))
        
        # References to other entries
        for prop_name, ref_list in self.references.items():
            for ref_id in ref_list:
                yield (subj, object_id(prop_name), object_id(ref_id))
