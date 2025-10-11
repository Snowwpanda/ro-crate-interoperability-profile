# RO-Crate Schema Library (Python)

This is the Python implementation of the RO-Crate Interoperability Profile, providing a Pythonic interface for creating, managing, and exporting RO-Crates with schema definitions and data files.

## Key Features

- **Pydantic Integration**: Define schemas using familiar Pydantic models with decorators
- **File Handling**: Built-in support for including data files in RO-Crates  
- **Schema Export**: Convert Pydantic models to RDFS/OWL schema definitions
- **RO-Crate I/O**: Import and export complete RO-Crates with metadata and files
- **Type Safety**: Strongly typed models with automatic validation
- **Round-trip Fidelity**: Import RO-Crates back to Python objects
- **Flexible API**: Both high-level decorator approach and low-level manual construction

## Installation

1. Make sure you install `astral-uv`
2. Move to the project folder [here](./)
3. Run the following commands
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Quick Start


### Method 1: Decorator Style (Recommended)

The decorator approach provides the most Pythonic and convenient way to define RO-Crate schemas:

```python
from lib_ro_crate_schema.crate.decorators import ro_crate_schema, Field
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from pydantic import BaseModel
from datetime import datetime

@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    name: str = Field(ontology="https://schema.org/name")
    email: str = Field(ontology="https://schema.org/email")
    affiliation: str = Field(comment="Research institution")

@ro_crate_schema(ontology="https://schema.org/Dataset")
class Experiment(BaseModel):
    title: str = Field(ontology="https://schema.org/name")
    date: datetime = Field(ontology="https://schema.org/dateCreated")
    researcher: Person = Field(ontology="https://schema.org/author")

# Create instances and export
person = Person(name="Dr. Alice Smith", email="alice@example.com", affiliation="MIT")
experiment = Experiment(
    title="Chemical Synthesis Study",
    date=datetime.now(),
    researcher=person
)

facade = SchemaFacade()
facade.add_all_registered_models()  # Automatically includes all @ro_crate_schema models
facade.add_model_instance(person, "researcher_001")
facade.add_model_instance(experiment, "experiment_001")
facade.add_file("data.csv", name="Experimental Results")
facade.write("my_research_crate")
```

### Method 2: Manual Construction

For fine-grained control or compatibility with existing code, you can manually construct Type, TypeProperty, and MetadataEntry objects:

```python
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.restriction import Restriction

# Create TypeProperty definitions
name_property = TypeProperty(
    id="name",
    range_includes=["http://www.w3.org/2001/XMLSchema#string"],
    ontological_annotations=["https://schema.org/name"],
    comment="Person's full name",
    required=True
)

email_property = TypeProperty(
    id="email", 
    range_includes=["http://www.w3.org/2001/XMLSchema#string"],
    ontological_annotations=["https://schema.org/email"],
    comment="Contact email address"
)

# Create restrictions
name_restriction = Restriction(
    property_type="name",
    min_cardinality=1,
    max_cardinality=1
)

# Create Type definition
person_type = Type(
    id="Person",
    ontological_annotations=["https://schema.org/Person"],
    rdfs_property=[name_property, email_property],
    restrictions=[name_restriction],
    comment="Represents a person in the research context"
)

# Create MetadataEntry (instance data)
person_entry = MetadataEntry(
    id="person_001",
    class_id="Person",
    properties={
        "name": "Dr. Alice Smith",
        "email": "alice@example.com"
    }
)

# Add to facade and export
facade = SchemaFacade()
facade.addType(person_type)
facade.addEntry(person_entry)
facade.write("manual_crate")
```



## Documentation

### Examples
- **[`full_example.py`](examples/full_example.py)** - Complex scientific workflow with OpenBIS hierarchy, file handling, and experimental synthesis simulation
- **[`python_quickstart.py`](examples/python_quickstart.py)** - Fluent builder API demonstrating manual Type, PropertyType, and MetadataEntry construction
- **[`decorator_example.py`](examples/decorator_example.py)** - Comprehensive @ro_crate_schema decorator usage with Person, Organization, and Publication models
- **[`architecture_demo.py`](examples/architecture_demo.py)** - Complete architecture flow demonstration showing Pydantic → RDF → RO-Crate transformations
- **[`export_pydantic_demo.py`](examples/export_pydantic_demo.py)** - Exporting Type definitions back to Pydantic model classes for dynamic code generation
- **[`minimal_import_example.py`](examples/minimal_import_example.py)** - Simple RO-Crate import example loading external openBIS crates
- **[`api_spec_test.py`](tests/api_spec_test.py)** - API specification compliance tests validating interface contracts and method signatures
- **[`examples.py`](examples/examples.py)** - Collection of smaller examples demonstrating specific features
- **[`rdf_lib_example.py`](examples/rdf_lib_example.py)** - Direct RDFLib integration for advanced RDF graph manipulation

### Tests
- **[`test_roundtrip.py`](tests/test_roundtrip.py)** - Round-trip fidelity tests ensuring export→import→export consistency
- **[`test_schema_facade.py`](tests/test_schema_facade.py)** - Core SchemaFacade functionality and file handling integration tests
- **[`test_integration.py`](tests/test_integration.py)** - End-to-end integration tests covering the complete workflow

## Schema API Quick Reference

### SchemaFacade
| Method | Description |
|--------|-------------|
| `add_all_registered_models()` | Add all @ro_crate_schema decorated models |
| `add_model_instance(instance, id)` | Add Pydantic instance as metadata entry |
| `addType(type_obj)` | Add Type definition to schema |
| `addEntry(entry)` | Add MetadataEntry to schema |
| `add_file(path, name, description)` | Add data file to be included in crate |
| `write(destination, name, description)` | Export complete RO-Crate with files |
| `to_graph()` | Generate RDFLib Graph representation |
| `from_ro_crate(path)` | Import existing RO-Crate |

### Type
| Method | Description |
|--------|-------------|
| `Type(id, ontological_annotations, rdfs_property)` | Create RDFS Class definition |
| `to_triples()` | Generate RDF triples for the Type |
| `resolve(resolver)` | Resolve forward references |

### TypeProperty  
| Method | Description |
|--------|-------------|
| `TypeProperty(id, range_includes, ontological_annotations)` | Create RDF Property definition |
| `to_triples()` | Generate RDF triples for the Property |
| `domain_includes` | Classes that can have this property |
| `range_includes` | Allowed value types for this property |

### MetadataEntry
| Method | Description |
|--------|-------------|
| `MetadataEntry(id, class_id, properties, references)` | Create instance metadata |
| `to_triples()` | Generate RDF triples for the instance |
| `properties` | Direct property values (strings, numbers) |
| `references` | References to other entities by ID |

### Restriction
| Method | Description |  
|--------|-------------|
| `Restriction(property_type, min_cardinality, max_cardinality)` | Create OWL cardinality constraint |
| `to_triples()` | Generate RDF triples for the restriction |

## Complete Example

For a comprehensive demonstration of all library capabilities, see [`examples/full_example.py`](examples/full_example.py). This example showcases:

- **Complex Scientific Workflow**: Complete OpenBIS-style hierarchy with Projects, Spaces, Collections, and Equipment
- **Chemical Synthesis Simulation**: Experimental workflow with molecule transformations
- **File Integration**: Automatic generation and inclusion of experimental observation data (CSV)
- **Self-referential Models**: Molecules containing other molecules, nested equipment relationships
- **Mixed Ontologies**: Combining custom OpenBIS namespaces with standard schema.org vocabularies
- **Round-trip Workflow**: Export → Import → Modify → Re-export cycle

Run with:
```bash
python examples/full_example.py
```

