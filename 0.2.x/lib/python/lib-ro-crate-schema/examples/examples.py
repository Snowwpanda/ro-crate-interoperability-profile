# Utility functions for reconstruction

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from rocrate.rocrate import ROCrate

from rdflib import Graph
from lib_ro_crate_schema.crate.jsonld_utils import add_schema_to_crate
# from lib_ro_crate_schema.crate import reconstruction  # Not available


def main():
    """
    Example demonstrating manual RO-Crate construction with automatic OWL restrictions.
    
    When manually creating TypeProperty objects, you can specify required=True/False
    to automatically generate OWL restrictions with appropriate cardinality constraints:
    - required=True  -> generates minCardinality: 1 (field is mandatory)
    - required=False -> generates minCardinality: 0 (field is optional)
    
    This ensures Java compatibility where OWL restrictions define field requirements.
    """
    
    # Define properties with cardinality information
    name = TypeProperty(
        id="name", 
        range_includes=[LiteralType.STRING],
        required=True,  # This will generate minCardinality: 1
        label="Full Name",
        comment="The full name of the entity"
    )
    identifier = TypeProperty(
        id="identifier", 
        range_includes=[LiteralType.STRING],
        required=True,  # This will generate minCardinality: 1
        label="Identifier", 
        comment="Unique identifier for the entity"
    )

    colleague = TypeProperty(
        id="colleague", 
        range_includes=["Participant"],
        required=False,  # This will generate minCardinality: 0 (optional)
        label="Colleague",
        comment="Optional colleague relationship"
    )

    participant_type = Type(
        id="Participant",
        type="Type",
        subclass_of=["https://schema.org/Thing"],
        ontological_annotations=["http://purl.org/dc/terms/creator"],
        rdfs_property=[name, identifier],
        comment="A participant in the research",
        label="Participant",
    )

    creator_type = Type(
        id="Creator",
        type="Type",
        subclass_of=["https://schema.org/Thing"],
        ontological_annotations=["http://purl.org/dc/terms/creator"],
        rdfs_property=[name, identifier, colleague],
        comment="A creator of the research work",
        label="Creator",
    )

    # Example MetadataEntry using new format with class_id and values
    creator_entry = MetadataEntry(
        id="creator1",
        class_id="Creator",
        values={
            "name": "John Author",
            "identifier": "https://orcid.org/0000-0000-0000-0000",
        },
        references={},
    )

    participant_entry = MetadataEntry(
        id="participant",
        class_id="Participant", 
        values={
            "name": "Karl Participant",
            "identifier": "https://orcid.org/0000-0000-0000-0001",
        },
        references={
            "colleague": ["creator1"]
        },
    )

    schema = SchemaFacade(
        types=[creator_type, participant_type],
        # properties=[has_name, has_identifier],
        metadata_entries=[creator_entry, participant_entry],
    )
    #Resolve refs
    schema.resolve_forward_refs()
    #Add it to a crate
    crate = ROCrate()
    crate.license = "a"
    crate.name = "mtcrate"
    crate.description = "test crate"
    crate = add_schema_to_crate(schema, crate)
    #Serialise - write to temp dir and read back for JSON output
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        crate.write(temp_dir)
        metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
        with open(metadata_file, 'r') as f:
            res = json.load(f)
    print(json.dumps(res))
    # Write to file
    import os
    output_dir = "output_crates"
    os.makedirs(output_dir, exist_ok=True)
    crate_path = os.path.join(output_dir, "example_crate")
    crate.write(crate_path)


# Use the reconstruction module's main entry point
def reconstruct(graph: Graph):
    # return reconstruction.reconstruct(graph)  # Not available
    raise NotImplementedError("Reconstruction module not available")


if __name__ == "__main__":
    main()
