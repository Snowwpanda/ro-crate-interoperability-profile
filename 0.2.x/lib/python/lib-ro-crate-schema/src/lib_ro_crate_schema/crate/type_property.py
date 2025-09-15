from enum import Enum
import itertools
from typing import Annotated, Iterable, List, Optional, Union, TYPE_CHECKING


from lib_ro_crate_schema.crate.rdf import SCHEMA, is_type, object_id
from lib_ro_crate_schema.crate.literal_type import LiteralType, to_rdf
from lib_ro_crate_schema.crate.registry import ForwardRef, Registry
from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator, create_model

from pydantic_rdf import BaseRdfModel, WithPredicate
from rdflib import BNode, Graph, Namespace, URIRef, RDF, RDFS, Literal, OWL, XSD, SDO

from pydantic import computed_field


MY_NS = Namespace("ro-schema")


class LiteralType(Enum):
    BOOLEAN = "xsd:boolean"
    INTEGER = "xsd:integer"
    DOUBLE = "xsd:double"
    DECIMAL = "xsd:decimal"
    FLOAT = "xsd:float"
    DATETIME = "xsd:dateTime"
    STRING = "xsd:string"
    XML_LITERAL = "rdf:XMLLiteral"

    def to_internal(self) -> URIRef:
        match self:
            case LiteralType.BOOLEAN:
                return XSD.boolean
            case LiteralType.INTEGER:
                return XSD.integer
            case LiteralType.DOUBLE:
                return XSD.double
            case LiteralType.DECIMAL:
                return XSD.decimal
            case LiteralType.FLOAT:
                return XSD.float
            case LiteralType.DATETIME:
                return XSD.dateTime
            case LiteralType.STRING:
                return XSD.string
            case LiteralType.XML_LITERAL:
                return RDF.XMLLiteral
            case _:
                raise ValueError(f"Unknown LiteralType: {self}")

    @classmethod
    def from_external(cls, value: str | URIRef | object) -> "LiteralType":
        """
        Import a LiteralType from an external representation.
        Accepts:
          - enum value (e.g. 'xsd:boolean')
          - full URI string (e.g. 'http://www.w3.org/2001/XMLSchema#boolean')
          - rdflib URIRef (e.g. XSD.boolean)
          - direct rdflib type (e.g. XSD.boolean)
        """
        match value:
            case str() as s:
                for lt in cls:
                    if s == lt.value:
                        return lt
                for lt in cls:
                    if s == str(lt.to_internal()):
                        return lt
            case URIRef() as u:
                for lt in cls:
                    if u == lt.to_internal():
                        return lt
            case _:
                for lt in cls:
                    if value is lt.to_internal():
                        return lt
        raise ValueError(f"No LiteralType for external value: {value}")


class RdfPropertyType(BaseRdfModel):
    rdf_type = RDF.Property
    _rdf_namespace = RDF
    label: Annotated[str | None, WithPredicate(RDFS.label)] = Field(...)
    range_includes: Annotated[
        list[Union[URIRef, "RdfType"]], WithPredicate(SDO.RangeIncludes)
    ] = Field(...)

    def to_external(self) -> "PropertyType":
        return PropertyType(
            id=self.uri,
            label=self.label,
            range_includes=[convert_range_to_external(r) for r in self.range_includes],
        )


def convert_range_to_external(
    range: Union[URIRef, "RdfType"],
) -> Union[LiteralType, "Type"]:
    match range:
        case URIRef() as ref:
            return LiteralType.from_external(ref)
        case RdfType() as rdf:
            return rdf.to_external()


def convert_range_to_internal(
    range: Union[LiteralType, "Type"],
) -> Union[URIRef, "RdfType"]:
    match range:
        case LiteralType() as lt:
            return lt.to_internal()
        case Type() as tp:
            return tp.to_internal()


class PropertyType(BaseModel):
    id: str
    label: str | None
    range_includes: list[Union[LiteralType, "Type"]]

    def to_internal(self) -> RdfPropertyType:
        return RdfPropertyType(
            uri=self.id,
            label=self.label,
            range_includes=[
                convert_range_to_internal(includes) for includes in self.range_includes
            ],
        )


class Restriction(BaseRdfModel):
    rdf_type = OWL.Restriction
    _rdf_namespace = MY_NS
    on_property: Annotated[RdfPropertyType, WithPredicate(OWL.onProperty)] = Field(...)
    min_cardinality: Annotated[int, WithPredicate(OWL.minCardinality)] = Field(...)
    max_cardinality: Annotated[int, WithPredicate(OWL.maxCardinality)] = Field(...)


class RdfType(BaseRdfModel):
    rdf_type = RDFS.Class
    _rdf_namespace = MY_NS
    equivalent_class: Annotated[str | None, WithPredicate(OWL.equivalentClass)] = Field(
        default=None
    )
    subclass_of: Annotated[list["RdfType"], WithPredicate(RDFS.subClassOf)] = Field(
        default=[]
    )
    label: Annotated[str | None, WithPredicate(RDFS.label)] = Field(None)
    comment: Annotated[str | None, WithPredicate(RDFS.comment)] = Field(default=None)
    restrictions: Annotated[list[Restriction], WithPredicate(OWL.Restriction)] = Field(
        default=[]
    )

    def to_external(self) -> "Type":
        pass


class Type(BaseModel):
    id: str
    equivalent_class: str = Field(default=None)
    subclass_of: list["Type"] = Field(default=[])
    label: str | None = Field(default=None)
    comment: str | None = Field(default=None)
    properties: list[PropertyType] = Field(default=[])

    def restrictions(self) -> list[Restriction]:
        return [
            Restriction(
                uri=BNode(),
                on_property=prop.to_internal(),
                min_cardinality=0,
                max_cardinality=1,
            )
            for prop in self.properties
        ]

    def to_internal(self) -> RdfType:
        restrictions: list[Restriction] = self.restrictions()
        return RdfType(
            uri=self.id,
            subclass_of=[c.to_internal() for c in self.subclass_of],
            label=self.comment,
            equivalent_class=self.equivalent_class,
            restrictions=restrictions,
        )


def generate_model

class MetadataEntry(BaseModel):
    id: str
    type: Type
    properties: dict[str, str | int | float | bool]

    def to_internal(self) -> BaseRdfModel:
        return RdfMetadataEntry.from_external(self)


create_model(__base__= BaseRdfModel)
# class RdfMetadataEntry(BaseRdfModel):
#     rdf_type: URIRef
#     properties: Annotated(dict[str, str], WithPredicate())
#     _rdf_namespace = MY_NS
#     @classmethod
#     def from_external(cls: type["RdfMetadataEntry"], external: MetadataEntry):
#         breakpoint()

#         return cls(
#             rdf_type=external.type.to_internal().uri,
#             uri=external.id,
#             **external.properties,
#         )


def merge_graphs_from_lists(*graph_lists: Iterable[list[Graph]]) -> Graph:
    merged = Graph()
    for g in itertools.chain.from_iterable(graph_lists):
        merged += g
    return merged


class SchemaFacade(BaseModel):
    types: List[Type]
    entries: List[MetadataEntry]

    def add_type(model: BaseModel):
        pass

    def to_rdf(self):
        rdf_types: list[Graph] = [t.to_internal().model_dump_rdf() for t in self.types]
        entries: list[Graph] = [md.to_internal().model_dump_rdf() for e in self.entries]
        merged = merge_graphs_from_lists(rdf_types + entries)
        return merged


t0 = Type(id="root", subclass_of=[])
p1 = PropertyType(id="d", label="a", range_includes=[LiteralType.INTEGER])
p2 = PropertyType(id="d1", label="a1", range_includes=[LiteralType.XML_LITERAL])
t1 = Type(id="c", equivalent_class="a", subclass_of=[t0], properties=[p1, p2])
md = MetadataEntry(id="a", type=t1, properties={"d": "a", "d1": "a"})

f1 = SchemaFacade(types=[t1], entries=[md])

g1 = f1.to_rdf()
print(g1.serialize(format="turtle"))
