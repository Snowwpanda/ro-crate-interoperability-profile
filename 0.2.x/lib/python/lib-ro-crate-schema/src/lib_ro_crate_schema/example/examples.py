from pathlib import Path
import tempfile
import json
from lib_ro_crate_schema.crate.rdf import BASE, SCHEMA, unbind
from lib_ro_crate_schema.crate.type import Type, RdfsClass
from lib_ro_crate_schema.crate.type_property import TypeProperty, RoTypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from rocrate.rocrate import ROCrate
from rocrate.model import ContextEntity
from rdflib import Graph, RDF
import pyld


RO_EXTRA_CTX = {
    "owl:minCardinality": {"@type": "xsd:integer"},
    "owl:maxCardinality": {"@type": "xsd:integer"},
}


def update_jsonld_context(ld_obj: dict, new_context: dict[str, str]) -> dict:
    """
    Use pyld to update the @context of a JSON-LD object.
    Returns a new JSON-LD object with the updated context.
    """
    return pyld.jsonld.compact(ld_obj, new_context)


def get_context(g: Graph) -> dict[str, str]:
    """
    Extracts all used namespaces from the rdflib graph and returns a JSON-LD @context dict.
    This can be used for JSON-LD compaction or as a base for RO-Crate @context.
    """
    # Get all namespaces used in the graph
    context = {}
    for prefix, namespace in g.namespaces():
        # Avoid default empty prefix
        if prefix:
            context[prefix] = str(namespace)
    # Optionally, add schema.org and other common ones if not present
    if "schema" not in context:
        context["schema"] = "https://schema.org/"
    return context


def emit_crate_with_context(crate: ROCrate, context: dict) -> dict:
    """
    Emits the ROCrate to a temporary file, reads it back, updates the @context directly (no pyld),
    and returns the updated JSON-LD dict. Uses the tempfile context manager for cleanup.
    """
    with tempfile.TemporaryDirectory() as tmp:
        crate.metadata.write(tmp)
        ld = json.loads((Path(tmp) / Path("ro-crate-metadata.json")).read_text())
        # Only allow old context as string (RO-Crate style), else raise error
        orig_ctx = ld.get("@context")
        if isinstance(orig_ctx, str):
            ld["@context"] = [orig_ctx, context]
        else:
            raise ValueError(
                f"Unsupported original @context type: {type(orig_ctx)}. Only string is supported for RO-Crate compatibility."
            )
        return ld
    return pyld.jsonld.compact(ld, context)


def add_schema_to_crate(schema: SchemaFacade, crate: ROCrate) -> dict:
    """
    Emits triples from schema, builds a graph, compacts JSON-LD, adds objects to the crate,
    writes to a tempfile, updates context using pyld, and returns the final JSON-LD dict.
    """
    triples = schema.to_triples()
    metadata_graph = Graph()
    metadata_graph.bind("base", BASE)
    for t in triples:
        metadata_graph.add(t)
    # Serialize and compact JSON-LD
    ld_ser = metadata_graph.serialize(format="json-ld")
    ld_obj = pyld.jsonld.json.loads(ld_ser)

    context = {**get_context(metadata_graph), **RO_EXTRA_CTX}
    ld_obj_compact = update_jsonld_context(ld_obj, context)
    # Add each object in the compacted graph to the crate
    for obj in ld_obj_compact.get("@graph", []):
        crate.add_jsonld(obj)
    # Use the tempfile-based utility to update context and return
    return emit_crate_with_context(crate, context)


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
