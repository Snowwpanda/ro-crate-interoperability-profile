# Technical Documentation

## Architecture Overview

`lib-ro-crate-schema` is a Python library that bridges Pydantic models with RO-Crate metadata standards. It provides a decorator-based approach to create semantically annotated research objects.

## Package Structure

```
lib_ro_crate_schema/
├── crate/
│   ├── decorators.py         # Schema decorators for Pydantic models
│   ├── schema_facade.py      # Main API for crate management
│   ├── schema_registry.py    # Global registry for type templates
│   ├── type.py               # Type definition and management
│   ├── type_property.py      # Property type definitions
│   ├── property_type.py      # Property metadata
│   ├── metadata_entry.py     # Metadata entry handling
│   ├── jsonld_utils.py       # JSON-LD conversion utilities
│   ├── rdf.py                # RDF graph generation
│   ├── restriction.py        # OWL restriction handling
│   ├── forward_ref_resolver.py  # Forward reference resolution
│   └── literal_type.py       # Literal type handling
└── check.py                  # Validation utilities
```

## Core Components

### 1. Decorators (`decorators.py`)

**Purpose**: Provide a clean decorator-based API for annotating Pydantic models with ontology information.

**Key Functions**:
- `@ro_crate_schema(ontology: str)`: Class decorator that registers a Pydantic model as an RO-Crate schema type
- `Field(json_schema_extra: dict, ...)`: Pydantic Field with RO-Crate metadata in json_schema_extra

**Flow**:
1. Decorator captures class definition
2. Extracts field annotations and ontology mappings from json_schema_extra
3. Creates `TypeTemplate` and registers in `SchemaRegistry`
4. Returns original class unchanged

**Example** (Pydantic 2.x compatible):
```python
@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    email: str = Field(json_schema_extra={"ontology": "https://schema.org/email"})
```


### 2. Schema Registry (`schema_registry.py`)

**Purpose**: Global singleton that maintains a registry of all decorated types and their ontological mappings.

**Key Classes**:
- `SchemaRegistry`: Singleton registry pattern
- `TypeTemplate`: Template containing type information and property mappings

**Key Methods**:
- `register_type(model, ontology)`: Register a new type template
- `get_type_template(model_name)`: Retrieve registered type
- `get_all_type_templates()`: Get all registered types

**Flow**:
```
Decorator → TypeTemplate Creation → Registry Storage → Facade Retrieval
```

### 3. Schema Facade (`schema_facade.py`)

**Purpose**: Main API for creating and managing RO-Crates. Provides high-level operations for schema and metadata management.

**Key Classes**:
- `SchemaFacade`: Primary interface for RO-Crate operations

**Key Methods**:
- `add_all_registered_models()`: Add all decorator-registered models to schema
- `add_model_instance(instance, id)`: Add a Pydantic instance as metadata
- `to_graph()`: Convert schema + metadata to RDF graph
- `from_ro_crate(path)`: Import existing RO-Crate
- `export(path)`: Export to directory (deprecated, use jsonld_utils)

**Internal State**:
- `types`: List of `Type` objects (schema definitions)
- `type_properties`: List of `TypeProperty` objects (property definitions)
- `metadata_entries`: List of `MetadataEntry` objects (actual data)

**Flow**:
```
SchemaFacade.add_all_registered_models()
    ↓
Retrieve from SchemaRegistry
    ↓
Convert TypeTemplate → Type + TypeProperty
    ↓
SchemaFacade.add_model_instance(person)
    ↓
Convert Pydantic instance → MetadataEntry
    ↓
SchemaFacade.to_graph()
    ↓
Generate RDF triples
```

### 4. Type System (`type.py`, `type_property.py`, `property_type.py`)

**Type (`type.py`)**:
- Represents an RDFS Class (e.g., `schema:Person`)
- Contains type properties and restrictions
- Generates RDF class definitions

**TypeProperty (`type_property.py`)**:
- Represents an RDF Property definition
- Links a property to its domain (type) and range (value type)
- Handles cardinality restrictions (min/max)

**PropertyType (`property_type.py`)**:
- Simple data class for property metadata
- Stores property name and RDF type

**Relationships**:
```
Type (Person)
  └── has TypeProperty (name)
        └── has PropertyType (string)
        └── has Restriction (minCardinality: 1)
```

### 5. Metadata Entry (`metadata_entry.py`)

**Purpose**: Represents an actual instance of data (not the schema).

**Key Attributes**:
- `id`: Unique identifier
- `class_id`: Reference to Type
- `properties`: Dict of property values
- `references`: List of referenced entities

**Flow**:
```
Pydantic Instance (person = Person(...))
    ↓
extract_from_pydantic()
    ↓
MetadataEntry
    ↓
to_triples()
    ↓
RDF Graph
```

### 6. JSON-LD Utilities (`jsonld_utils.py`)

**Purpose**: Convert between RO-Crate (JSON-LD) and internal representations.

**Key Functions**:
- `add_schema_to_crate(facade, crate)`: Merge schema/metadata into ROCrate object
- Handles context management
- Converts RDF graph to JSON-LD @graph array

**Flow**:
```
SchemaFacade → RDF Graph → JSON-LD @graph → ROCrate.write()
```

### 7. RDF Generation (`rdf.py`)

**Purpose**: Convert schema and metadata to RDF triples.

**Key Functions**:
- `to_graph()`: Main conversion function
- Creates RDF graph with proper namespaces
- Handles OWL restrictions, class hierarchies, property definitions

**Output**: RDFLib Graph object with schema + data triples

### 8. Forward Reference Resolution (`forward_ref_resolver.py`)

**Purpose**: Handle Pydantic forward references (e.g., `creator: "Person"` when Person is defined later).

**Key Classes**:
- `ForwardRefResolver`: Resolves string type hints to actual classes

**When Used**: During TypeTemplate creation when processing nested models

### 9. Restriction (`restriction.py`)

**Purpose**: Model OWL restrictions (cardinality constraints).

**Key Classes**:
- `Restriction`: Represents OWL constraints on properties
- `RestrictionType`: Enum of restriction types (min/max cardinality)

**Flow**:
```
Pydantic Field (required vs Optional)
    ↓
Determine cardinality
    ↓
Create Restriction object
    ↓
Generate OWL:Restriction triples
```

## Data Flow

### Complete Export Flow

```
1. Model Definition
   @ro_crate_schema(...)
   class Person(BaseModel): ...
   ↓
2. Registration
   TypeTemplate → SchemaRegistry
   ↓
3. Facade Creation
   facade = SchemaFacade()
   facade.add_all_registered_models()
   ↓
4. Add Instances
   person = Person(...)
   facade.add_model_instance(person, "alice")
   ↓
5. RDF Generation
   graph = facade.to_graph()
   ↓
6. JSON-LD Conversion
   crate = ROCrate()
   final_crate = add_schema_to_crate(facade, crate)
   ↓
7. Export
   final_crate.write(path)
```

### Complete Import Flow

```
1. Read RO-Crate
   path = "crate_directory/"
   ↓
2. Parse JSON-LD
   ROCrate.read(path)
   ↓
3. Import to Facade
   facade = SchemaFacade.from_ro_crate(path)
   ↓
4. Extract Schema
   facade.types → Type objects
   facade.type_properties → TypeProperty objects
   ↓
5. Extract Metadata
   facade.metadata_entries → MetadataEntry objects
   ↓
6. Query/Modify
   Access entities via facade
```

## Key Design Patterns

### 1. Decorator Pattern
- Non-intrusive model annotation
- Preserves Pydantic functionality
- Automatic registration

### 2. Facade Pattern
- `SchemaFacade` provides simplified interface
- Hides internal complexity of RDF/OWL generation
- Single entry point for operations

### 3. Registry Pattern
- `SchemaRegistry` maintains global type catalog
- Singleton ensures consistency
- Enables decoupled type lookup

### 4. Builder Pattern
- Incremental construction of RO-Crates
- Add types, properties, metadata step-by-step
- Flexible composition

## Extension Points

### Adding Custom Types

```python
@ro_crate_schema(ontology="https://example.org/CustomType")
class CustomType(BaseModel):
    custom_field: str = Field(json_schema_extra={ontology="https://example.org/customField"})
```

### Custom Property Types

Extend `PropertyType` for specialized property handling.

### Custom Restrictions

Extend `Restriction` class for additional OWL constraints.

## Performance Considerations

- **Registry Lookups**: O(1) hash-based lookups
- **RDF Generation**: Linear in number of entities + properties
- **Memory**: Stores full graph in memory (consider streaming for large crates)

## Dependencies

- **pydantic**: Model definition and validation
- **rdflib**: RDF graph manipulation
- **rocrate**: RO-Crate standard implementation
- **pyld**: JSON-LD processing
- **pyshacl**: SHACL validation

## Testing Strategy

- **Unit Tests**: Test individual components (Type, TypeProperty, etc.)
- **Integration Tests**: Test full export/import cycles
- **Round-trip Tests**: Ensure export → import → export produces identical results
- **Published Package Tests**: Verify installability from PyPI

## Common Pitfalls

1. **Forgetting to call `add_all_registered_models()`**: Models won't appear in schema
2. **Circular references**: Use forward references carefully
3. **ID conflicts**: Ensure unique IDs when adding instances
4. **Context mixing**: RO-Crate context vs custom contexts

## Debugging Tips

- Use `facade.to_graph()` to inspect RDF triples
- Check `SchemaRegistry.get_all_type_templates()` to see registered types
- Validate JSON-LD output with online validators
- Use `pyshacl` for SHACL validation

## Future Enhancements

- Streaming support for large datasets
- SHACL shape generation from Pydantic models
- Query API for metadata
- Incremental updates to existing crates
- Better circular reference handling
