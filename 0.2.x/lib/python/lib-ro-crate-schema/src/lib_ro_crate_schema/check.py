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
    parser.add_argument("data_file", type=Path)
    parser.add_argument("shape_file", type=Path)
    parser.add_argument("data_format", type=DataFormat)
    args = parser.parse_args()
    data_path = args.data_file
    shape_path = args.shape_file
    data_format = args.data_format

    data_graph = load_graph(data_path, DataFormat.JSONLD)
    shape_graph = load_graph(shape_path, DataFormat.TURTLE)
    print(data_graph.all_nodes())
    print(shape_graph.all_nodes())

    conforms, results_graph, results_text = validate(
        data_graph=data_graph,
        shacl_graph=shape_graph,
        debug=True,
        serialize_report_graph=True,
    )

    print("✔ Conforms" if conforms else "✘ Does NOT conform")
    print(results_text)

    if not conforms:
        sys.exit(1)


if __name__ == "__main__":
    main()
