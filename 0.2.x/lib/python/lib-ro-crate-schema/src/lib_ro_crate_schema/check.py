import sys
import json
from rdflib import Graph
from pyshacl import validate
from pyld import jsonld
from argparse import ArgumentParser
from pathlib import Path
from enum import Enum


class DataFormat(Enum):
    JSONLD = "json-ld"
    TURTLE = "ttl"


def load_graph(path: Path, fmt: DataFormat) -> Graph:
    g = Graph()
    match fmt:
        case DataFormat.JSONLD:
            g.parse(location=path, format="json-ld")
        case DataFormat.TURTLE:
            g.parse(location=path, format="turtle")
    return g


def main():
    parser = ArgumentParser("Check a RO-crate-profile file for conformity")
    parser.add_argument("data_file", type=Path, help="RDF data file to validate")
    parser.add_argument("--shape-file", type=Path, default=None, 
                       help="SHACL shapes file (default: tests/schema.shacl)")
    parser.add_argument("--format", type=DataFormat, default=DataFormat.TURTLE,
                       help="Data format (json-ld or ttl)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed validation results")
    args = parser.parse_args()
    
    data_path = args.data_file
    data_format = args.format
    
    # Default to our updated SHACL schema
    if args.shape_file:
        shape_path = args.shape_file
    else:
        # Look for schema.shacl in tests directory
        current_dir = Path(__file__).parent
        shape_path = current_dir.parent.parent / "tests" / "schema.shacl"
        
    print(f"🔍 Validating: {data_path}")
    print(f"📐 Using SHACL: {shape_path}")
    print(f"📄 Data format: {data_format.value}")
    
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        sys.exit(1)
        
    if not shape_path.exists():
        print(f"❌ SHACL file not found: {shape_path}")
        print("   Use --shape-file to specify a custom SHACL schema")
        sys.exit(1)

    try:
        data_graph = load_graph(data_path, data_format)
        shape_graph = load_graph(shape_path, DataFormat.TURTLE)
        
        print(f"✅ Loaded {len(data_graph)} data triples")
        print(f"✅ Loaded {len(shape_graph)} SHACL constraint triples")
        
    except Exception as e:
        print(f"❌ Error loading graphs: {e}")
        sys.exit(1)

    print("\n🔍 Running SHACL validation...")
    
    conforms, results_graph, results_text = validate(
        data_graph=data_graph,
        shacl_graph=shape_graph,
        debug=args.verbose,
        serialize_report_graph=True,
    )

    if conforms:
        print("✅ VALIDATION PASSED - Data conforms to SHACL schema!")
        print(f"   📊 {len(data_graph)} triples validated successfully")
    else:
        print("❌ VALIDATION FAILED - Constraint violations found:")
        print(results_text)
        
        if results_graph and args.verbose:
            print(f"\n📋 Generated {len(results_graph)} validation result triples")

    if not conforms:
        sys.exit(1)


if __name__ == "__main__":
    main()
