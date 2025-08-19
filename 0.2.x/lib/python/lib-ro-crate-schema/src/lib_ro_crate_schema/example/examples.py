from collections import defaultdict
import json
from lib_ro_crate_schema.crate.rdf import BASE
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from rocrate.rocrate import ROCrate
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Node
from lib_ro_crate_schema.crate.jsonld_utils import (
    add_schema_to_crate,
)


def main():
    has_name = TypeProperty(id="hasName", range_includes_data_type=[LiteralType.STRING])
    has_identifier = TypeProperty(
        id="hasIdentifier", range_includes_data_type=[LiteralType.STRING]
    )

    creator_type = Type(
        id="Creator",
        type="Type",
        subclass_of=["https://schema.org/Thing"],
        ontological_annotations=["http://purl.org/dc/terms/creator"],
        rdfs_property=[has_name, has_identifier],
        comment="",
        label="",
    )

    participant_type = Type(
        id="Participant",
        type="Type",
        subclass_of=["https://schema.org/Thing"],
        ontological_annotations=["http://purl.org/dc/terms/creator"],
        rdfs_property=[has_name, has_identifier],
        comment="",
        label="",
    )

    # Example MetadataEntry using property and type references (object and string)
    creator_entry = MetadataEntry(
        id="creator1",
        types=[creator_type],
        props={
            "has_name": "John Author",
            "has_identifier": "https://orcid.org/0000-0000-0000-0000",
        },
        references={},
    )

    participant_entry = MetadataEntry(
        id="participant",
        types=[participant_type],
        props={
            "hasName": "Karl Participant",
            "hasIdentifier": "https://orcid.org/0000-0000-0000-0001",
        },
        references={},
    )

    schema = SchemaFacade(
        types=[creator_type, participant_type],
        # properties=[has_name, has_identifier],
        metadata_entries=[creator_entry, participant_entry],
    )

    crate = ROCrate()
    crate.license = "a"
    crate.name = "mtcrate"
    crate.description = "test crate"
    res = add_schema_to_crate(schema, crate)

    schema_graph = schema.to_graph()
    reconstruct(schema_graph)
    print(json.dumps(res))


def reconstruct(graph: Graph) -> SchemaFacade:
    # Utility functions for reconstruction
    def get_subjects_by_type(graph: Graph, rdf_type: Node) -> set[Node]:
        """Return all subjects of a given rdf:type."""
        return set(graph.subjects(RDF.type, rdf_type))

    def get_predicate_object_map(graph: Graph, subject: Node) -> dict[URIRef, Node]:
        """Return a dict of predicate -> object for a given subject."""
        return {p: o for p, o in graph.predicate_objects(subject)}
    # Reconstruct in correct order: Classes, Properties, Restrictions, Metadata Entries

    print("Reconstructing Classes:")
    for class_subject in get_subjects_by_type(graph, RDFS.Class):
        props = get_predicate_object_map(graph, class_subject)
        print(f"  Class: {class_subject}, {props}")
        # Here you would instantiate Type(...)

    print("Reconstructing Properties:")
    for prop_subject in get_subjects_by_type(graph, RDF.Property):
        props = get_predicate_object_map(graph, prop_subject)
        print(f"  Property: {prop_subject}, {props}")
        # Here you would instantiate TypeProperty(...)

    print("Reconstructing Restrictions:")
    for restr_subject in get_subjects_by_type(graph, OWL.Restriction):
        props = get_predicate_object_map(graph, restr_subject)
        print(f"  Restriction: {restr_subject}, {props}")
        # Here you would handle restrictions

    # Example: reconstructing metadata entries if you have a special type
    # for entry_subject in get_subjects_by_type(graph, PROFILE.MetadataEntry):
    #     props = get_predicate_object_map(graph, entry_subject)
    #     print(f"  MetadataEntry: {entry_subject}, {props}")

    breakpoint()



if __name__ == "__main__":
    main()
