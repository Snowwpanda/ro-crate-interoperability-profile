from lib_ro_crate_schema.crate.ro import RO_ID_LITERAL
from pydantic import BaseModel, Field
from rdflib.graph import Node
from rdflib import URIRef, RDF, Literal
from lib_ro_crate_schema.crate.rdf import is_type

class MetadataEntry(BaseModel):
    id: str 
    props: dict[str, str] 
    references: dict[str, list[str]] | None = None
    children_identifiers: list[str] | None = None
    parent_identifiers: list[str] | None = None

    def to_triples(self, subject=None):
        subj = URIRef(self.id) if subject is None else subject
        if self.types:
            for t in self.types:
                yield is_type(self.id, URIRef(t))
        if self.props:
            for p, v in self.props.items():
                yield (subj, URIRef(p), Literal(v))
        if self.references:
            for p, vs in self.references.items():
                for v in vs:
                    yield (subj, URIRef(p), URIRef(v))
