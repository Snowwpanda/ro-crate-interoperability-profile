# 🧪 RO-Crate Full Example Guide

**File:** `examples/full_example.py`

Comprehensive example demonstrating advanced RO-Crate features: chemical synthesis workflow, circular relationships, SHACL validation, and dynamic updates.

## 📊 **Data Model**

#### **OpenBIS Entities** (`http://openbis.org/`)

| Entity | Properties | Relationships |
|--------|------------|---------------|
| **Project** | code, name, description, created_date | → space |
| **Space** | name, description, created_date | → collections[] |
| **Collection** | name, sample_type, storage_conditions, created_date | _(leaf node)_ |
| **Equipment** | name, model, serial_number, created_date, configuration{} | → parent_equipment |

#### **Schema.org Entities** (`https://schema.org/`)

| Entity | Properties | Relationships |
|--------|------------|---------------|
| **Molecule** | name, **smiles**, molecular_weight, cas_number, created_date, experimental_notes | → contains_molecules[] |
| **Person** | name, orcid, email | → affiliation |
| **Organization** | name, country, website | _(referenced by Person)_ |
| **Publication** | title, doi, publication_date | → authors[], molecules[], equipment[], organization |

## ⚡ **Workflow: Setup → Experiment → Export**

**Created Entities:**
- 1 Project, 1 Space, 1 Collection, 2 Equipment (nested)
- 5 Molecules, 2 People, 1 Organization, 1 Publication

**Key Features:**
- ✅ **Circular Relationships**: Person ↔ Person colleagues (auto-resolved)
- ✅ **Mixed Namespaces**: OpenBIS + schema.org with auto-context
- ✅ **SHACL Validation**: 100% compliance with 150+ rules
- ✅ **Dynamic Updates**: Experiment modifies molecules + adds new product

## 🔧 **Key Technical Features**

### **1. Circular Relationship Resolution**
```python
# Automatic resolution of Person ↔ Person colleagues
sarah = Person(colleagues=[marcus])
marcus = Person(colleagues=[sarah])
# → SchemaFacade.resolve_placeholders() merges duplicates
```

### **2. Chemical Data with SMILES**
- Benzene: `c1ccccc1` → Toluene: `Cc1ccccc1` → Product: `(c1ccccc1).(Cc1ccccc1)`

### **3. Scale Metrics**
- **Entities**: 15 → 16 (after synthesis)
- **RDF Triples**: ~500 → ~530 
- **SHACL Validation**: 100% compliance


## � **Usage**

```bash
PYTHONPATH=./src python examples/full_example.py
```

**Output:** 
Initial Crate: `full_example_initial/`
Final Crate: `full_example_final/` including file [experimental_observations](examples/experimental_observations.csv)

## ✅ **Testing**

```bash
python -m pytest tests/ -v                    # Full suite (85 tests)
```

---

**Production-ready RO-Crate library with automatic relationship resolution, comprehensive validation, and modern architecture.**