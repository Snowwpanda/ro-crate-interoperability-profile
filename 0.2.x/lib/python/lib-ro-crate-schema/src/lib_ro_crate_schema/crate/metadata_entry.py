from pydantic import BaseModel, Field
from rdflib.graph import Node
from rdflib import URIRef, RDF, Literal
from lib_ro_crate_schema.crate.rdf import is_type, object_id


from typing import Union
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.type import Type


class MetadataEntry(BaseModel):
    id: str
    # props: property reference (TypeProperty or str) -> value
    props: dict[Union[TypeProperty, str], str]
    # Types can be either strings or directly references to Type (RDF Types)
    types: list[Union[Type, str]]
    # references: property reference (TypeProperty or str) -> list of type references (Type or str)
    references: dict[Union[TypeProperty, str], list[Union[Type, str]]] | None = None
    children_identifiers: list[str] | None = None
    parent_identifiers: list[str] | None = None

    def to_triples(self):
        subj = object_id(self.id)
        for current_type in self.types:
            match current_type:
                case str(tid):
                    yield is_type(self.id, URIRef(tid))
                case Type(id=tid):
                    yield is_type(self.id, URIRef(tid))
        for prop_name, prop_value in self.props.items():
            yield (subj, object_id(prop_name), Literal(prop_value))
