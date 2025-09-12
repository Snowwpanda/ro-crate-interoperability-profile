from enum import Enum
import itertools
from typing import Annotated, Iterable, List, Optional, Union, TYPE_CHECKING


from lib_ro_crate_schema.crate.rdf import SCHEMA, is_type, object_id
from lib_ro_crate_schema.crate.literal_type import LiteralType, to_rdf
from lib_ro_crate_schema.crate.registry import ForwardRef, Registry
from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator

from pydantic_rdf import BaseRdfModel, WithPredicate
from rdflib import BNode, Graph, Namespace, URIRef, RDF, RDFS, Literal, OWL, XSD

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


class RdfPropertyType(BaseRdfModel):
    rdf_type = RDF.Property
    _rdf_namespace = RDF
    label: Annotated[str | None, WithPredicate(RDFS.label)] = Field(...)
    range_includes: Annotated[
        list[Union[URIRef, "RdfType"]], WithPredicate(SCHEMA.RangeIncludes)
    ] = Field(...)

    def to_external(self) -> "PropertyType":
        return PropertyType(id=self.uri, label=self.label, )



def convert_range(range: LiteralType | "Type") -> URIRef | "RdfType":
    match range:
        case LiteralType() as lt:
            return lt.to_internal()
        case Type() as tp:
            return tp.to_internal()


class PropertyType(BaseModel):
    id: str
    label: str | None
    range_includes: Union[LiteralType | "Type"]

    def to_internal(self) -> RdfPropertyType:
        return RdfPropertyType(
            uri=self.id,
            label=self.label,
            range_includes=[
                convert_range(includes) for includes in self.range_includes
            ],
        )


class Restriction(BaseRdfModel):
    rdf_type = OWL.Restriction
    _rdf_namespace = MY_NS
    on_property: Annotated[TypeProperty, WithPredicate(OWL.onProperty)] = Field(...)
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


class Type(BaseModel):
    id: str
    equivalent_class: str = Field(default=None)
    subclass_of: list["Type"] = Field(default=[])
    label: str | None = Field(default=None)
    comment: str | None = Field(default=None)
    properties: list[TypeProperty] = Field(default=[])

    def restrictions(self) -> list[Restriction]:
        return [
            Restriction(
                uri=BNode(), on_property=prop, min_cardinality=0, max_cardinality=1
            )
            for prop in self.properties
        ]

    def to_internal(self) -> RdfType:
        restrictions: list[Restriction] = self.restrictions()
        breakpoint()
        return RdfType(
            uri=self.id,
            subclass_of=[c.to_internal() for c in self.subclass_of],
            label=self.comment,
            equivalent_class=self.equivalent_class,
            restrictions=restrictions,
        )


def merge_graphs_from_lists(*graph_lists: Iterable[list[Graph]]) -> Graph:
    merged = Graph()
    for g in itertools.chain.from_iterable(graph_lists):
        merged += g
    return merged


class SchemaFacade(BaseModel):
    types: List[Type]

    def to_rdf(self):
        rdf_types: list[Graph] = [t.to_internal().model_dump_rdf() for t in self.types]
        breakpoint()
        merged = merge_graphs_from_lists(rdf_types)
        return merged


t0 = Type(id="root", subclass_of=[])
p1 = PropertyType(uri="d", label="a", range_includes=[LiteralType.INTEGER])
p2 = PropertyType(uri="d1", label="a1", range_includes=[LiteralType.XML_LITERAL])
t1 = Type(id="c", equivalent_class="a", subclass_of=[t0], properties=[p1, p2])


class Molecule(BaseModel):
    SMILES: str


""""

1. Importing

#Gives you all types that exsits in the crate
crate.get_types() -> List[BaseModel]:

#Reads in an object given a Pydantic BaseModel (which is defined on the receiving side)
# (Static workflow if we know that we have a structrually compatible type)
crate.read_as(Molecule, my_crate, id) -> Molecule | None:

2. Exporting

# Will add the schema to a crate
create.add_to_schema(Molecule)

m1 = Molecule()

#Will add the metadat and the schema to the crate
crate.add(m1) 


3. Manual /  Fine Grained implementation (for conformity with the Java Implementation)

p1 = Property(...)
t1 = Type(properties=[p1,...])

4. Confortimy:
Internally we convert into RdfsClasses and RdfTypes
and we expose a java style API for conformity with the openBIS requirements.
The export is valid by definiton because we generate valid rdf and add it to a ro-crate

""""


f1 = SchemaFacade(types=[t1])

g1 = f1.to_rdf()
print(g1.serialize(format="turtle"))


# class TypeProperty(BaseModel):
#     id: str
#     label: Optional[str] = None
#     comment: Optional[str] = None
#     _domain_includes: Optional[List[ForwardRef["Type"]]] = None  # internal use only
#     range_includes: Optional[List[Union[LiteralType, ForwardRef["Type"], "Type"]]] = (
#         None
#     )
#     ontological_annotations: Optional[List[str]] = None

#     @field_validator("range_includes", mode="before")
#     @classmethod
#     def wrap_forward_refs(
#         cls, v: Optional[List[Union[LiteralType, ForwardRef["Type"]]]]
#     ):
#         """
#         Allows the user-facing API to specify the forward reference as a string
#         """
#         match v:
#             case None:
#                 return v
#             case els:
#                 values = []
#                 for range_element in els:
#                     match range_element:
#                         case LiteralType():
#                             values.append(range_element)
#                         case ForwardRef(ref):
#                             values.append(range_element)
#                         case str(ref):
#                             values.append(ForwardRef(ref=ref))
#                 return values

#     @property
#     def domain_includes(self) -> Optional[List[str]]:
#         # For serialization only
#         return self._domain_includes

#     # @property
#     # def range_includes(self) -> Optional[List[str]]:
#     #     # For serialization only
#     #     return self._range_includes

#     def resolve(self, registry: Registry):
#         """
#         Resolve all references to types
#         """
#         from lib_ro_crate_schema.crate.type import Type
#         range_includes = []
#         domain_includes = []
#         for range_element in self.range_includes:
#             match range_element:
#                 case Type() | LiteralType():
#                     range_includes.append(range_element)
#                 case ForwardRef():
#                     print(range_element)
#                     range_includes.append(registry.resolve(range_element))
#                 case _:
#                     raise TypeError(
#                         f"Unsupported range_includes element: {range_element!r}"
#                     )

#         for domain_element in self._domain_includes if self._domain_includes else []:
#             match domain_element:
#                 case Type():
#                     domain_includes.append(domain_element)
#                 case ForwardRef():
#                     domain_element.append(registry.resolve(domain_element))
#                 case _:
#                     raise TypeError(
#                         f"Unsupported range_includes element: {domain_element!r}"
#                     )
#         self._domain_includes = domain_includes
#         self.range_includes = range_includes

#     def _resolve_range_includes(self):
#         """ """
#         from lib_ro_crate_schema.crate.type import Type

#         resolved = []
#         if not self.range_includes:
#             return resolved
#         for range_element in self.range_includes:
#             match range_element:
#                 case Type(id=tid):
#                     resolved.append(object_id(tid))
#                 case LiteralType():
#                     resolved.append(to_rdf(range_element))
#                 case str(ref):
#                     resolved.append(URIRef(ref))
#                 case _:
#                     raise TypeError(
#                         f"Unsupported range_includes element: {range_element!r}"
#                     )
#         return resolved

#     def to_triples(self, subject=None):
#         subj = object_id(self.id) if subject is None else subject
#         yield (subj, RDF.type, RDF.Property)
#         if self.label:
#             yield (subj, RDFS.label, Literal(self.label))
#         if self.comment:
#             yield (subj, RDFS.comment, Literal(self.comment))
#         if self.domain_includes:
#             for d in self.domain_includes:
#                 yield (subj, SCHEMA.domainIncludes, URIRef(d))
#         for r in self._resolve_range_includes():
#             print(type(r), r)
#             yield (subj, SCHEMA.rangeIncludes, r)
#         if self.ontological_annotations:
#             for r in self.ontological_annotations:
#                 yield (subj, OWL.equivalentClass, URIRef(r))
#         # Add more as needed for data types, annotations, etc.
