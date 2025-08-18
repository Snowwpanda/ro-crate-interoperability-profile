import tempfile
import json
from pathlib import Path
import pyld

def emit_crate_with_context(crate, context):
    """
    Emits the ROCrate to a temporary file, reads it back, updates the @context directly (no pyld),
    and returns the updated JSON-LD dict. Uses the tempfile context manager for cleanup.
    Only supports original @context as string (RO-Crate style).
    """
    with tempfile.TemporaryDirectory() as tmp:
        crate.metadata.write(tmp)
        ld = json.loads((Path(tmp) / Path("ro-crate-metadata.json")).read_text())
    orig_ctx = ld.get("@context")
    if isinstance(orig_ctx, str):
        ld["@context"] = [orig_ctx, context]
    else:
        raise ValueError(f"Unsupported original @context type: {type(orig_ctx)}. Only string is supported for RO-Crate compatibility.")
    return ld

def update_jsonld_context(ld_obj, new_context):
    """
    (Legacy) Use pyld to update the @context of a JSON-LD object.
    Returns a new JSON-LD object with the updated context.
    """
    return pyld.jsonld.compact(ld_obj, new_context)

def get_context(g):
    """
    Extracts all used namespaces from the rdflib graph and returns a JSON-LD @context dict.
    This can be used for JSON-LD compaction or as a base for RO-Crate @context.
    """
    context = {}
    for prefix, namespace in g.namespaces():
        if prefix:
            context[prefix] = str(namespace)
    if "schema" not in context:
        context["schema"] = "https://schema.org/"
    return context

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
