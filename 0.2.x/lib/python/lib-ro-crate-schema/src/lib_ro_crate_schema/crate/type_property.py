from typing import List, Optional, Union

from lib_ro_crate_schema.crate.rdf import SCHEMA, is_type, object_id
from lib_ro_crate_schema.crate.ro_constants import DOMAIN_IDENTIFIER
from .literal_type import LiteralType, to_rdf
from pydantic import BaseModel, Field
from rocrate.model import Person
from rocrate.model.contextentity import ContextEntity

from rdflib import URIRef, RDF, RDFS, Literal, OWL



class TypeProperty(BaseModel):
    id: str
    label: Optional[str] = None
    comment: Optional[str] = None
    domain_includes: Optional[List[str]] = None
    range_includes: Optional[List[str]] = None
    range_includes_data_type: Optional[List[LiteralType]] = None
    ontological_annotations: Optional[List[str]] = None

    def to_triples(self, subject=None):
        subj = object_id(self.id) if subject is None else subject
        yield (subj, RDF.type, RDF.Property)
        if self.label:
            yield (subj, RDFS.label, Literal(self.label))
        if self.comment:
            yield (subj, RDFS.comment, Literal(self.comment))
        if self.domain_includes:
            for d in self.domain_includes:
                yield (subj, SCHEMA.domainIncludes,  URIRef(d))
        if self.range_includes:
            for r in self.range_includes:
                yield (subj, SCHEMA.rangeIncludes, URIRef(r))
        if self.range_includes_data_type:
            for r in self.range_includes_data_type:
                yield (subj, SCHEMA.rangeIncludes, to_rdf(r))
        if self.ontological_annotations:
            for r in self.ontological_annotations:
                yield (subj, OWL.equivalentClass, URIRef(r))
        # Add more as needed for data types, annotations, etc.


