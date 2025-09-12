# Placeholder

This is the Python implementation


## How to work on the project

1. Make sure you install `astral-uv`
2. Move to the project folder [here](./)
3. Run the following commands
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```


# Crate I/O API Guide

This library provides a Pythonic interface for importing and exporting objects to and from a RO-Crate using the extension profile.
Unlike the Java implementation, which relies heavily on builder patterns, this API integrates naturally with Pydantic models and standard Python workflows.

The result is cleaner, more idiomatic code that avoids the verbosity and “stringly-typed” style typical of Java builders, while still ensuring full compatibility with the openBIS requirements.

---

## Importing

You can inspect the contents of a crate and deserialize objects into strongly typed Pydantic models.

### List available types

Assuming we have imported our crate into `crate`, we can do:

  ```python
  from pydantic import BaseModel
  crate.get_types() -> List[BaseModel]
  ```

This returns all object types defined in the crate as a list of BaseModels. This could be used for codegen since a basemodel can be exported as a JSON Schema and used to generate the class definitions.

### Read an object as a given type**
Assuming we have a an avialable `Molecule`, `BaseModel`, we can do:

```python
crate.read_as(Molecule, my_crate, id) -> Molecule | None
```

This call deserializes an object into the specified Pydantic model (`Molecule` in this case).

This is a *static workflow*: it requires that the receiving side knows the type and that it is structurally compatible.

This approach lets developers work directly with familiar Python models rather than manually navigating RDF structures.

If the class is not available, one needs to create them for example by inspecting the output of `get_types`.

---

## Exporting

Exporting models to a crate is possible in two ways:

### Register a schema only

One can add a schema to a crate by passing a BaseModel:

```python
crate.add_to_schema(Molecule)
```

This will add the definition to the crate.

### Add an object instance

One can also pass directly an instance of a `BaseModel`.

```python
m1 = Molecule()
crate.add(m1)
```

This automatically adds both the schema and the object’s metadata to the crate. Developers work with native Python objects, while the library ensures that valid RDF is generated and inserted.

---

## Fine-Grained / Manual Mode

For cases where strict parity with the Java API is required, the library also allows manual construction:

```python
p1 = Property(...)
t1 = Type(properties=[p1, ...])
```

This low-level interface mirrors the Java implementation, but is rarely needed in typical Python workflows.

---

##  Conformity and Interoperability

Internally, the library converts objects into `RdfsClasses` and `RdfTypes`.
A Java-style API is exposed where necessary to meet openBIS interoperability requirements.

However, the **preferred approach in Python** is to work with Pydantic models and high-level functions (`read_as`, `add`, `add_to_schema`). This avoids boilerplate, reduces errors, and provides strong validation guarantees out of the box.

---

## Why the Pythonic Approach Is Better

* **Java style**: verbose builders, string references, manual wiring.
* **Python style**: typed models, declarative APIs, validation by design.

Both approaches remain interoperable, but the Pythonic path is safer, faster, and more natural for data-driven workflows.
