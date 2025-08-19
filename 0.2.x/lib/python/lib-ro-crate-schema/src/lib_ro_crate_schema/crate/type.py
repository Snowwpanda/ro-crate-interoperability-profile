from typing import List, Generator

from lib_ro_crate_schema.crate.rdf import is_type, object_id
from .restriction import Restriction
from .type_property import TypeProperty
from pydantic import BaseModel
from rdflib import Node, Literal, URIRef, RDFS, OWL


class Type(BaseModel):
    id: str
    type: str
    subclass_of: List[str] | None
    ontological_annotations: List[str] | None
    rdfs_property: List[TypeProperty] | None
    comment: str
    label: str

    def get_restrictions(self) -> list[Restriction]:
        """
        Get the restrictions that
        represent the properties of this type (RDFS:Class)
        """
        return [
            Restriction(property_type=prop.id, min_cardinality=1, max_cardinality=1)
            for prop in self.rdfs_property
            if self.rdfs_property
        ]

    def to_triples(self) -> Generator[Node]:
        """
        Emits the type definition as a set of triples
        whose subject is a RDFS:Class
        """

        yield is_type(self.id, RDFS.Class)
        yield (object_id(self.id), RDFS.comment, Literal(self.comment))
        yield (object_id(self.id), RDFS.label, Literal(self.label))
        annotations = [
            (object_id(self.id), OWL.equivalentClass, URIRef(cls))
            for cls in self.ontological_annotations
        ]
        for ann in annotations:
            yield ann
        for restriction in self.get_restrictions():
            yield from restriction.to_triples()
        for prop in self.rdfs_property:
            prop_with_domain = prop.model_copy(update=dict(domain_includes=[self.id]))
            yield from prop_with_domain.to_triples()

    # def to_ro(self) -> RdfsClass:
    #     return RdfsClass(id=self.id,
    #               self_type="rdfs:Class",
    #               subclass_of=serialize_references(self.subclass_of),
    #               #rdfs_properties=[prop.to_ro() for prop in self.rdfs_property] if self.rdfs_property is not None else None,
    #               ontological_annotations=None)

    # def to_ro(self):
    #     return RdfsClass(
    #         id=RoId(id=self.id),
    #         subclass_of=[RoId(id=i) for i in self.subclass_of if i] if self.subclass_of else [],
    #         ontological_annotations=
    #         equivalent_class=
    #     )
