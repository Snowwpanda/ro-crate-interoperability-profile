from typing import Optional
from lib_ro_crate_schema.crate.rdf import is_type, object_id, Triple

from pydantic import BaseModel, Field, ConfigDict
from rdflib import OWL, Literal, XSD
from uuid import uuid4


class Restriction(BaseModel):
    """
    Represents an OWL Restriction that constrains how properties can be used on classes.
    
    OWL Restrictions are a fundamental part of ontological modeling, allowing precise specification
    of property constraints such as cardinality (how many values are allowed), type constraints,
    and value restrictions. These are essential for RO-Crate schema validation and semantic modeling.
    
    Key Responsibilities:
    - Define cardinality constraints (minimum/maximum number of values)
    - Specify which property the restriction applies to
    - Generate proper OWL RDF triples for semantic validation
    - Support both required properties (minCardinality >= 1) and optional properties (minCardinality = 0)
    - Enable precise schema validation in RO-Crate profiles
    
    Common Restriction Patterns:
    - Required single value: min_cardinality=1, max_cardinality=1
    - Required multiple values: min_cardinality=1, max_cardinality=None (unlimited)
    - Optional single value: min_cardinality=0, max_cardinality=1
    - Optional multiple values: min_cardinality=0, max_cardinality=None
    
    Usage Example:
        # Create a restriction requiring exactly one name property
        name_restriction = Restriction(
            property_type="name",
            min_cardinality=1,
            max_cardinality=1
        )
        
        # Create a restriction allowing multiple optional emails
        email_restriction = Restriction(
            property_type="email",
            min_cardinality=0,
            max_cardinality=None  # unlimited
        )
        
    JSON-LD Output Example:
        {
            "@id": "Person_name_restriction",
            "@type": "owl:Restriction",
            "owl:onProperty": {"@id": "name"},
            "owl:minCardinality": 1,
            "owl:maxCardinality": 1
        }
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    property_type: str
    min_cardinality: Optional[int] = None
    max_cardinality: Optional[int] = None

    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )

    def to_triples(self):
        """Generate RDF triples for this OWL restriction"""
        subj = object_id(self.id)
        yield is_type(self.id, OWL.Restriction)
        yield (subj, OWL.onProperty, object_id(self.property_type))
        
        # Only emit cardinality constraints that are actually set
        if self.min_cardinality is not None:
            yield (
                subj,
                OWL.minCardinality,
                Literal(self.min_cardinality, datatype=XSD.integer),
            )
        
        if self.max_cardinality is not None:
            yield (
                subj,
                OWL.maxCardinality,
                Literal(self.max_cardinality, datatype=XSD.integer),
            )
