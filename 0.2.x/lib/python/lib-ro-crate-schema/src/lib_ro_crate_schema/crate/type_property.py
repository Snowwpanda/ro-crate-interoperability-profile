from typing import List, Optional, Union, TYPE_CHECKING


from lib_ro_crate_schema.crate.rdf import SCHEMA, is_type, object_id
from lib_ro_crate_schema.crate.literal_type import LiteralType, to_rdf
from lib_ro_crate_schema.crate.registry import ForwardRef, Registry
from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator

from rdflib import URIRef, RDF, RDFS, Literal, OWL

if TYPE_CHECKING:
    from lib_ro_crate_schema.crate.type import Type


class TypeProperty(BaseModel):
    id: str
    label: Optional[str] = None
    comment: Optional[str] = None
    _domain_includes: Optional[List[ForwardRef["Type"]]] = None  # internal use only
    range_includes: Optional[List[Union[LiteralType, ForwardRef["Type"], "Type"]]] = (
        None
    )
    ontological_annotations: Optional[List[str]] = None

    @field_validator("range_includes", mode="before")
    @classmethod
    def wrap_forward_refs(
        cls, v: Optional[List[Union[LiteralType, ForwardRef["Type"]]]]
    ):
        """
        Allows the user-facing API to specify the forward reference as a string
        """
        match v:
            case None:
                return v
            case els:
                values = []
                for range_element in els:
                    match range_element:
                        case LiteralType():
                            values.append(range_element)
                        case ForwardRef(ref):
                            values.append(range_element)
                        case str(ref):
                            values.append(ForwardRef(ref=ref))
                return values

    @property
    def domain_includes(self) -> Optional[List[str]]:
        # For serialization only
        return self._domain_includes

    # @property
    # def range_includes(self) -> Optional[List[str]]:
    #     # For serialization only
    #     return self._range_includes

    def resolve(self, registry: Registry):
        """
        Resolve all references to types
        """
        from lib_ro_crate_schema.crate.type import Type
        range_includes = []
        domain_includes = []
        for range_element in self.range_includes:
            match range_element:
                case Type() | LiteralType():
                    range_includes.append(range_element)
                case ForwardRef():
                    print(range_element)
                    range_includes.append(registry.resolve(range_element))
                case _:
                    raise TypeError(
                        f"Unsupported range_includes element: {range_element!r}"
                    )
        
        for domain_element in self._domain_includes if self._domain_includes else []:
            match domain_element:
                case Type():
                    domain_includes.append(domain_element)
                case ForwardRef():
                    domain_element.append(registry.resolve(domain_element))
                case _:
                    raise TypeError(
                        f"Unsupported range_includes element: {domain_element!r}"
                    )
        self._domain_includes = domain_includes
        self.range_includes = range_includes

    def _resolve_range_includes(self):
        """ """
        from lib_ro_crate_schema.crate.type import Type

        resolved = []
        if not self.range_includes:
            return resolved
        for range_element in self.range_includes:
            match range_element:
                case Type(id=tid):
                    resolved.append(object_id(tid))
                case LiteralType():
                    resolved.append(to_rdf(range_element))
                case str(ref):
                    resolved.append(URIRef(ref))
                case _:
                    raise TypeError(
                        f"Unsupported range_includes element: {range_element!r}"
                    )
        return resolved

    def to_triples(self, subject=None):
        subj = object_id(self.id) if subject is None else subject
        yield (subj, RDF.type, RDF.Property)
        if self.label:
            yield (subj, RDFS.label, Literal(self.label))
        if self.comment:
            yield (subj, RDFS.comment, Literal(self.comment))
        if self.domain_includes:
            for d in self.domain_includes:
                yield (subj, SCHEMA.domainIncludes, URIRef(d))
        for r in self._resolve_range_includes():
            print(type(r), r)
            yield (subj, SCHEMA.rangeIncludes, r)
        if self.ontological_annotations:
            for r in self.ontological_annotations:
                yield (subj, OWL.equivalentClass, URIRef(r))
        # Add more as needed for data types, annotations, etc.
