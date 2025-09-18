from __future__ import annotations

from enum import Enum
import itertools
from typing import Annotated, Any, Iterable, List, Optional, Union, TYPE_CHECKING


from lib_ro_crate_schema.crate.rdf import SCHEMA, is_type, object_id
from lib_ro_crate_schema.crate.literal_type import LiteralType, to_rdf
from lib_ro_crate_schema.crate.registry import ForwardRef, Registry
from pydantic import (
    AnyUrl,
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    create_model,
)

from pydantic_rdf import BaseRdfModel, WithPredicate
from rdflib import BNode, Graph, Namespace, URIRef, RDF, RDFS, Literal, OWL, XSD, SDO

import re
from urllib.parse import urlparse
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional, Iterable

from pydantic import create_model
from pydantic_rdf import BaseRdfModel, WithPredicate
from rdflib import URIRef

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


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _safe_field_name(iri: str) -> str:
    """
    Make a safe Python identifier from an IRI:
        - prefer fragment; else last path segment
        - replace non-word chars with '_'
        - prefix 'f_' if empty or starts with a digit
        - preserve camelCase (no forced snake_case)
    """
    parsed = urlparse(iri)
    candidate = parsed.fragment or parsed.path.rsplit("/", 1)[-1]
    candidate = re.sub(r"\W", "_", candidate)
    if not candidate or candidate[0].isdigit():
        candidate = f"f_{candidate}"
    return candidate


def _python_type_for_range(rng) -> type:
    """
    Map your model's range types to Python types expected by pydantic-rdf.
    - LiteralType  -> Python scalar
    - Type         -> URIRef (object property)
    """
    match rng:
        # Literal ranges
        case LiteralType.BOOLEAN:
            return bool
        case LiteralType.INTEGER:
            return int
        case LiteralType.DOUBLE:
            return float
        case LiteralType.DECIMAL:
            return Decimal
        case LiteralType.FLOAT:
            return float
        case LiteralType.DATETIME:
            return datetime
        case LiteralType.STRING:
            return str
        case LiteralType.XML_LITERAL:
            return str  # or a custom XML wrapper

        # Object range (points to another resource of some Type)
        case Type():
            return URIRef

        case _:
            raise TypeError(f"Unsupported range: {rng!r}")


def _union_type_for_ranges(ranges: list[LiteralType | Type]) -> type:
    """
    Build a PEP 604 union (A | B | ...) from the allowed ranges.
    """
    ts = tuple(_python_type_for_range(r) for r in ranges)
    base = ts[0]
    for t in ts[1:]:
        base = base | t
    return base


def _cardinality_for_prop(t: Type, prop: PropertyType) -> tuple[int, Optional[int]]:
    """
    Extract (min, max) from your Type.restrictions(). Defaults to (0, 1).
    """
    for r in t.restrictions():
        # r.on_property is an RdfPropertyType; compare by URI string
        if str(r.on_property.uri) == str(prop.id):
            return r.min_cardinality, r.max_cardinality
    return 0, 1


def _maybe_sequence_type(base_t: type, min_c: int, max_c: Optional[int]) -> type:
    """
    If cardinality allows multiple values, use list[base_t].
    """
    if max_c is None or max_c > 1 or min_c > 1:
        return list[base_t]
    return base_t


def _maybe_optional(base_t: type, min_c: int) -> type:
    """
    Make Optional[...] when min=0 and not already a list[...] type.
    """
    match base_t:
        case list(x):
            return base_t
        case _:
            return base_t | None if min_c == 0 else base_t


def build_entry_model_for_type(t: Type) -> type[BaseRdfModel]:
    """
    Create a BaseRdfModel subclass whose fields correspond to the properties
    of the given Type, each annotated with WithPredicate(URIRef(prop.id)).
    """
    cls_name = _safe_field_name(t.id) + "Entry"

    # shell
    Base = create_model(  # type: ignore[call-arg]
        cls_name,
        __base__=BaseRdfModel,
        __module__=__name__,
    )

    # fix rdf:type at class level as expected by pydantic-rdf
    setattr(Base, "rdf_type", URIRef(t.id))

    # build fields
    fields: dict[str, tuple[type, object]] = {}
    for prop in t.properties:
        base_t = _union_type_for_ranges(prop.range_includes)
        min_c, max_c = _cardinality_for_prop(t, prop)
        base_t = _maybe_sequence_type(base_t, min_c, max_c)
        base_t = _maybe_optional(base_t, min_c)

        annotated_t = Annotated[base_t, WithPredicate(URIRef(prop.id))]
        fields[_safe_field_name(prop.id)] = (annotated_t, None)

    # finalize subclass with attached fields
    return create_model(  # type: ignore[call-arg]
        cls_name,
        __base__=Base,
        __module__=__name__,
        **fields,
    )


# ---------------------------------------------------------------------------
# factory
# ---------------------------------------------------------------------------


class MetadataEntry(BaseModel):
    """
    High-level, schema-driven entry:
      - id: IRI of the node
      - type: Type (with properties)
      - properties: values keyed by property IRI, label, or safe field name
    """

    id: Union[AnyUrl, str] = Field(...)
    type: Type
    properties: dict[str, dict | int | str | float] = Field(default_factory=dict)

    @field_validator("id", mode="before")
    @classmethod
    def _normalize_id(cls, v: Any) -> str:
        # Accept AnyUrl, URIRef, str
        match v:
            case URIRef():
                return str(v)
            case _:
                return str(v)

    # Convenience API
    def to_internal(self) -> BaseRdfModel:
        """Build the concrete BaseRdfModel instance (flattened triples)."""
        return RdfMetadataEntryFactory.from_external(self)

    def to_graph(self, g: Graph | None = None) -> Graph:
        """Serialize directly to an rdflib Graph."""
        g = g or Graph()
        self.to_rdf().to_graph(g)
        return g


class RdfMetadataEntryFactory:
    """
    Turn a high-level MetadataEntry into a concrete BaseRdfModel instance
    with flattened RDF predicates (no nested dict).
    """

    @staticmethod
    def from_external(entry: MetadataEntry) -> BaseRdfModel:
        Model = build_entry_model_for_type(entry.type)

        # accept incoming keys as exact IRI, label, or sanitized field name
        def _value_for(prop: PropertyType):
            for k in (prop.id, prop.label, _safe_field_name(prop.id)):
                if k is None:
                    continue
                if (val := entry.properties.get(k)) is not None:
                    return val
            return None

        kwargs = {
            _safe_field_name(prop.id): v
            for prop in entry.type.properties
            if (v := _value_for(prop)) is not None
        }

        return Model(uri=entry.id, **kwargs)


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


t0 = Type(id="Object", subclass_of=[])
p1 = PropertyType(id="count", label="count", range_includes=[LiteralType.INTEGER])
p2 = PropertyType(id="name", label="name", range_includes=[LiteralType.STRING])
t1 = Type(id="MyType", equivalent_class="a", subclass_of=[t0], properties=[p1, p2])
md = MetadataEntry(id="a", type=t1, properties={"count": 3, "name": "e"})

f1 = SchemaFacade(types=[t1], entries=[md])

g1 = f1.to_rdf()
print(g1.serialize(format="json-ld"))
