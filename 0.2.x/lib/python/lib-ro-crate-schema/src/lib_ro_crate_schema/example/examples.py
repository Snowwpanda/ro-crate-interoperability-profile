# Utility functions for reconstruction

import json
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from rocrate.rocrate import ROCrate

from rdflib import Graph
from lib_ro_crate_schema.crate.jsonld_utils import add_schema_to_crate
from lib_ro_crate_schema.crate import reconstruction


def main():
    has_name = TypeProperty(id="hasName", range_includes=[LiteralType.STRING])
    has_identifier = TypeProperty(
        id="hasIdentifier", range_includes=[LiteralType.STRING]
    )

    has_colleague = TypeProperty(id="hasColleague", range_includes=["Participant"])

    participant_type = Type(
        id="Participant",
        type="Type",
        subclass_of=["https://schema.org/Thing"],
        ontological_annotations=["http://purl.org/dc/terms/creator"],
        rdfs_property=[has_name, has_identifier],
        comment="",
        label="",
    )

    creator_type = Type(
        id="Creator",
        type="Type",
        subclass_of=["https://schema.org/Thing"],
        ontological_annotations=["http://purl.org/dc/terms/creator"],
        rdfs_property=[has_name, has_identifier, has_colleague],
        comment="",
        label="",
    )

    # Example MetadataEntry using property and type references (object and string)
    creator_entry = MetadataEntry(
        id="creator1",
        types=[creator_type, participant_type],
        props={
            "has_name": "John Author",
            "has_identifier": "https://orcid.org/0000-0000-0000-0000",
        },
        references={},
    )

    participant_entry = MetadataEntry(
        id="participant",
        types=[participant_type, creator_type],
        props={
            "hasName": "Karl Participant",
            "hasIdentifier": "https://orcid.org/0000-0000-0000-0001",
            "hasColleague": "creator1",
        },
        references={},
    )

    schema = SchemaFacade(
        types=[creator_type, participant_type],
        # properties=[has_name, has_identifier],
        metadata_entries=[creator_entry, participant_entry],
    )
    #Resolve refs
    schema.resolve_forward_refs()
    breakpoint()
    #Add it to a crate
    crate = ROCrate()
    crate.license = "a"
    crate.name = "mtcrate"
    crate.description = "test crate"
    res = add_schema_to_crate(schema, crate)
    #Serialise
    print(json.dumps(res))


# Use the reconstruction module's main entry point
def reconstruct(graph: Graph):
    return reconstruction.reconstruct(graph)


if __name__ == "__main__":
    main()
