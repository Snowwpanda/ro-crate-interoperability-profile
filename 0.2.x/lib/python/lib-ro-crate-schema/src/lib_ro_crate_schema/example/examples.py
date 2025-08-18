import json
from lib_ro_crate_schema.crate.rdf import BASE
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from rocrate.rocrate import ROCrate
from rdflib import Graph
from lib_ro_crate_schema.crate.jsonld_utils import (
    add_schema_to_crate,
    emit_crate_with_context,
    update_jsonld_context,
    get_context,
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

    # Example with string property references (for flexibility)
    creator_entry_str = MetadataEntry(
        id="creator2",
        types=[creator_type],
        props={
            "hasName": "Jane Author",
            "hasIdentifier": "https://orcid.org/0000-0000-0000-0001",
        },
        references={},
    )

    schema = SchemaFacade(
        types=[creator_type],
        properties=[has_name, has_identifier],
        metadata_entries=[creator_entry, creator_entry_str],
    )

    crate = ROCrate()
    crate.license = "a"
    crate.name = "mtcrate"
    crate.description = "test crate"
    res = add_schema_to_crate(schema, crate)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
