# RO-Crate Schema Library

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Pythonic library for creating and managing [RO-Crates](https://www.researchobject.org/ro-crate/).

**🚀 New to RO-Crate? Start with the [Quick Start Guide](QUICKSTART.md)!**

## What is it?

This library provides an interface for creating RO-Crates (Research Object Crates) a community standard for packaging research data with their metadata. Additionally to conventional crates, it allows to easily add objects of custom types (not present in Schema.org) and encode them as RDF according to the [profile](../../../spec.md). 
The modules offers two interface to operate with crates:

1. Pydantic models with decorators to declaratively define schemas that automatically generate RDF/OWL definitions. 
2. Pogrammatic builder-style interfaces for integration with other tooling or for working with objects whose schema isn't known at *compile time*.

## Installation

### From PyPI (recommended)

```bash
pip install lib-ro-crate-schema
```

### From Source

```bash
git clone https://github.com/Snowwpanda/ro-crate-interoperability-profile.git
cd ro-crate-interoperability-profile/0.2.x/lib/python/lib-ro-crate-schema
pip install -e .
```

## Quick Start

Here's a minimal example to get you started:

```python
from lib_ro_crate_schema import SchemaFacade, ro_crate_schema, Field
from pydantic import BaseModel

# Define your schema using decorators
@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    name: str = Field(ontology="https://schema.org/name")
    email: str = Field(ontology="https://schema.org/email")

# Create an instance
person = Person(name="Dr. Alice Smith", email="alice@example.com")

# Export to RO-Crate
facade = SchemaFacade()
facade.add_all_registered_models()  # Register all @ro_crate_schema models
facade.add_model_instance(person, "person_001")
facade.write("my_research_crate")
```

This creates a complete RO-Crate with:
- `ro-crate-metadata.json` containing your data and schema
- Proper RDF/OWL definitions
- Schema.org ontology mappings

## Key Features

✨ **Pydantic Integration** - Define schemas using familiar Pydantic models  
📦 **File Handling** - Include data files alongside metadata  
🔄 **Round-trip Support** - Import and re-export RO-Crates without data loss  
🏷️ **Ontology Mapping** - Map to standard vocabularies (Schema.org, custom ontologies)  
🔒 **Type Safety** - Strong typing with automatic validation  
📊 **RDF Export** - Generate RDFS/OWL schema definitions

## More Examples

### Including Data Files

```python
facade.add_file("experiment_data.csv", name="Experimental Results", 
                description="Raw data from chemical synthesis experiment")
facade.write("my_crate")
```

### Complex Relationships

```python
@ro_crate_schema(ontology="https://schema.org/Organization")
class Organization(BaseModel):
    name: str = Field(ontology="https://schema.org/name")

@ro_crate_schema(ontology="https://schema.org/Person")  
class Person(BaseModel):
    name: str = Field(ontology="https://schema.org/name")
    affiliation: Organization = Field(ontology="https://schema.org/affiliation")

org = Organization(name="MIT")
person = Person(name="Alice", affiliation=org)

facade = SchemaFacade()
facade.add_all_registered_models()
facade.add_model_instance(org, "org_001")
facade.add_model_instance(person, "person_001")
facade.write("my_crate")
```

### Importing Existing RO-Crates

```python
from lib_ro_crate_schema import SchemaFacade

facade = SchemaFacade.from_ro_crate("path/to/existing_crate")
# Modify and re-export
facade.write("modified_crate")
```

## Documentation

- **[Full Examples](examples/)** - Comprehensive examples including scientific workflows
- **[API Reference](src/lib_ro_crate_schema/)** - Detailed API documentation
- **[Tests](tests/)** - Test suite demonstrating all features

### Running Examples

```bash
# Simple decorator example
python examples/decorator_example.py

# Complex scientific workflow with file handling
python examples/full_example.py

# Import/export demonstration  
python examples/minimal_import_example.py
```

### Running Tests

```bash
# All tests
python run_all_tests.py

# Or with pytest
pytest tests/
```

## Advanced Usage

### Manual Construction (without decorators)

For fine-grained control, you can manually construct Type, TypeProperty, and MetadataEntry objects. This is useful for example when constructing objects from other schemas like SQL or JSON schemas, which don't immediately correspond to pydantic models. You can use it like this:

```python
from lib_ro_crate_schema import SchemaFacade, Type, TypeProperty, MetadataEntry

# Create property definition
name_property = TypeProperty(
    id="name",
    range_includes=["http://www.w3.org/2001/XMLSchema#string"],
    ontological_annotations=["https://schema.org/name"]
)

# Create type definition  
person_type = Type(
    id="Person",
    ontological_annotations=["https://schema.org/Person"],
    rdfs_property=[name_property]
)

# Create instance data
person_entry = MetadataEntry(
    id="person_001",
    class_id="Person", 
    properties={"name": "Alice"}
)

facade = SchemaFacade()
facade.addType(person_type)
facade.addEntry(person_entry)
facade.write("manual_crate")
```

See [`examples/python_quickstart_write.py`](examples/python_quickstart_write.py) for more details.

## API Overview

### Core Classes

| Class | Purpose |
|-------|---------|
| `SchemaFacade` | Main interface for creating and exporting RO-Crates |
| `Type` | Define RDFS classes (schema types) |
| `TypeProperty` | Define RDF properties for types |
| `MetadataEntry` | Instance data conforming to a Type |
| `Restriction` | OWL cardinality and property restrictions |

### Decorators (Recommended)

| Decorator | Purpose |
|-----------|---------|
| `@ro_crate_schema` | Mark Pydantic model as RO-Crate schema type |
| `Field` | Enhanced Pydantic Field with ontology mapping |

### SchemaFacade Methods

```python
facade = SchemaFacade()

# Decorator API
facade.add_all_registered_models()           # Add all @ro_crate_schema models
facade.add_model_instance(instance, id)      # Add Pydantic instance

# Manual API
facade.addType(type_obj)                     # Add Type definition
facade.addEntry(entry)                       # Add MetadataEntry

# File handling
facade.add_file(path, name, description)     # Include data file

# Export
facade.write(destination)                    # Write complete RO-Crate
facade.to_graph()                            # Get RDFLib Graph

# Import
SchemaFacade.from_ro_crate(path)            # Load existing RO-Crate
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this library in your research, please cite:

```bibtex
@software{ro_crate_schema,
  title = {RO-Crate Schema Library},
  author = {Baffelli, Simone and Su, Pascal},
  year = {2025},
  url = {https://github.com/Snowwpanda/ro-crate-interoperability-profile}
}
```

## Links

- **Repository**: https://github.com/Snowwpanda/ro-crate-interoperability-profile
- **RO-Crate Specification**: https://www.researchobject.org/ro-crate/
- **Pydantic Documentation**: https://docs.pydantic.dev/

