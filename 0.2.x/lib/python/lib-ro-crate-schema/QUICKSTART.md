# Quick Start Guide

Get started with `lib-ro-crate-schema` in 5 minutes!

## Installation

```bash
pip install lib-ro-crate-schema
```

## Your First RO-Crate

Create a file called `my_first_crate.py`:

```python
from lib_ro_crate_schema import SchemaFacade, ro_crate_schema, Field
from pydantic import BaseModel

# 1. Define your data model with decorators
@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    name: str = Field(ontology="https://schema.org/name")
    email: str = Field(ontology="https://schema.org/email")

# 2. Create some data
alice = Person(name="Alice Smith", email="alice@example.com")

# 3. Create and export an RO-Crate
facade = SchemaFacade()
facade.add_all_registered_models()  # Register your models
facade.add_model_instance(alice, "person_001")  # Add data
facade.write("my_first_crate")  # Export!

print("✅ RO-Crate created in ./my_first_crate/")
```

Run it:
```bash
python my_first_crate.py
```

This creates a folder `my_first_crate/` containing:
- `ro-crate-metadata.json` - Your data and schema in JSON-LD format
- Proper RDF/OWL type definitions
- Schema.org vocabulary mappings

## Next Steps

### Add Files to Your Crate

```python
# Add a data file before writing
facade.add_file("data.csv", 
                name="Experimental Data",
                description="Raw measurements")
facade.write("my_crate")
```

### Define Related Objects

```python
@ro_crate_schema(ontology="https://schema.org/Organization")
class Organization(BaseModel):
    name: str = Field(ontology="https://schema.org/name")

@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    name: str = Field(ontology="https://schema.org/name")
    affiliation: Organization = Field(ontology="https://schema.org/affiliation")

# Create related objects
mit = Organization(name="MIT")
alice = Person(name="Alice", affiliation=mit)

# Export both
facade = SchemaFacade()
facade.add_all_registered_models()
facade.add_model_instance(mit, "org_001")
facade.add_model_instance(alice, "person_001")
facade.write("my_crate")
```

### Import and Modify Existing Crates

```python
from lib_ro_crate_schema import SchemaFacade

# Load existing crate
facade = SchemaFacade.from_ro_crate("existing_crate")

# Modify it
# (add more instances, files, etc.)

# Export modified version
facade.write("modified_crate")
```

## What Just Happened?

When you use `@ro_crate_schema`:
1. Your Pydantic model is registered as an RO-Crate type
2. Field annotations map to ontology properties (like Schema.org)
3. The library generates proper RDF/OWL definitions
4. Your data is packaged following the RO-Crate specification

## More Examples

Check out the `examples/` directory:
- `decorator_example.py` - More complex schemas
- `full_example.py` - Scientific workflow with files
- `minimal_import_example.py` - Working with existing crates

## Common Patterns

### Optional Fields
```python
from typing import Optional

@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    name: str = Field(ontology="https://schema.org/name")
    email: Optional[str] = Field(default=None, ontology="https://schema.org/email")
```

### Lists
```python
from typing import List

@ro_crate_schema(ontology="https://schema.org/Dataset")
class Dataset(BaseModel):
    name: str = Field(ontology="https://schema.org/name")
    authors: List[Person] = Field(ontology="https://schema.org/author")
```

### Dates and Times
```python
from datetime import datetime

@ro_crate_schema(ontology="https://schema.org/Event")
class Event(BaseModel):
    name: str = Field(ontology="https://schema.org/name")
    date: datetime = Field(ontology="https://schema.org/startDate")
```

## Need Help?

- **Full Documentation**: See [README.md](README.md)
- **API Reference**: Browse the [src/lib_ro_crate_schema/](src/lib_ro_crate_schema/) directory
- **Examples**: Check [examples/](examples/) for real-world usage
- **Issues**: Report bugs at [GitHub Issues](https://github.com/Snowwpanda/ro-crate-interoperability-profile/issues)

## Understanding RO-Crate

RO-Crate (Research Object Crate) is a standard for packaging research data with metadata. It uses:
- **JSON-LD**: Linked data format
- **Schema.org**: Standard vocabulary for describing things
- **RDF/OWL**: Semantic web technologies

This library makes it easy to create RO-Crates from Python without needing to understand all these technologies!

---

**Ready for more?** Check out the full [README.md](README.md) for advanced usage and API details.
