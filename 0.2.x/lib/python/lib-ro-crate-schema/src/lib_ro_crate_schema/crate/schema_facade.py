# Constants from Java SchemaFacade
from collections import defaultdict
from pathlib import Path
from typing import Generator, Literal, Optional, Type as TypingType, Union, List
from types import ModuleType
import json
import tempfile
from datetime import datetime

from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.rdf import BASE, Triple, object_id
from lib_ro_crate_schema.crate.forward_ref_resolver import ForwardRefResolver
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.restriction import Restriction
from lib_ro_crate_schema.crate.schema_registry import get_schema_registry, TypeTemplate
from pydantic import BaseModel, Field, PrivateAttr
from lib_ro_crate_schema.crate.rdf import SCHEMA
from rdflib import RDFS, RDF, Graph
from rocrate.rocrate import ROCrate

from lib_ro_crate_schema.crate.forward_ref_resolver import ForwardRef
from typing import Any
from typing import List, Tuple

TypeRegistry = List[Tuple[TypeProperty, Type]]


def types_to_triples(used_types: TypeRegistry) -> Generator[Triple, None, None]:
    """
    Emits all the triples
    that represent the types found in the TypeRegistry
    Each key is a TypeProperty, each value is a list of Type objects using it.
    """
    for property_obj, cls in used_types:
        prop_with_domain = property_obj.model_copy(
            update=dict(domain_includes=[cls.id])
        )
        yield from prop_with_domain.to_triples()


class SchemaFacade(BaseModel):
    """
    Main RO-Crate Schema Facade - Central orchestrator for types, properties, restrictions, and metadata entries.
    Supports automatic schema generation from decorated Pydantic models and provides full Java API compatibility.
    
    Key Responsibilities:
    - Manage RDFS Classes (Type objects) and Properties (TypeProperty objects)
    - Store standalone properties and restrictions not attached to specific types
    - Store and query RDF Metadata Entries (MetadataEntry objects)
    - Generate RO-Crate JSON-LD output
    - Convert Pydantic models to RDF schema representations
    - Handle file attachments for RO-Crate data files
    
    Commonly Used Methods:
    
    **Schema Management:**
    - addType(type_obj) -> Add RDFS Class definition
    - add_property_type(property) -> Add standalone property
    - add_restriction(restriction) -> Add standalone restriction
    - addEntry(entry) -> Add RDF metadata entry
    - get_types() -> List all RDFS Classes
    - get_property_types() -> List all properties (standalone + type-attached)
    - get_restrictions() -> List all restrictions (standalone + type-attached)
    - get_property_type(id) -> Find specific property by ID
    - get_restriction(id) -> Find specific restriction by ID
    - get_entries() -> List all metadata entries
    - get_entry(id) -> Find specific metadata entry
    - get_entries_by_class(class_id) -> Find entries of specific type
    
    **File Management:**
    - add_file(file_path, name=None, description=None) -> Add file to be included in crate
    - get_files() -> List all files to be included
    - clear_files() -> Remove all file references
    
    **Pydantic Integration:**
    - add_pydantic_model(model_class) -> Convert Pydantic model to RDFS schema
    - add_model_instance(instance) -> Convert Pydantic instance to metadata entry
    - add_registered_models(*names) -> Add models from decorator registry
    - add_all_registered_models() -> Add all registered models
    
    **Export & Serialization:**
    - write(destination) -> Export complete RO-Crate to file
    - to_json() -> Get JSON-LD representation
    - to_graph() -> Get RDF Graph representation
    - to_triples() -> Get RDF triple iterator
    
    **Java API Compatibility (ISchemaFacade):**
    - get_crate() -> Get complete ROCrate object with schema and files integrated
    - getCrate() -> Alias for get_crate() (Java API compatibility)
    - getType(id) -> Get specific RDFS Class
    - getPropertyTypes() -> Get all properties (includes standalone)
    - getPropertyType(id) -> Get specific property by ID
    - getRestrictions() -> Get all restrictions (includes standalone)
    - getRestriction(id) -> Get specific restriction by ID
    
    Usage Example:
        facade = SchemaFacade()
        facade.addType(person_type)
        facade.addEntry(person_instance)
        facade.add_file("data.csv", name="Experimental Data")
        facade.write('my-crate')
        
    Complete RO-Crate Output Structure Example:
        {
            "@context": [
                "https://w3id.org/ro/crate/1.1/context",
                {
                    "base": "http://example.com/",
                    "owl:maxCardinality": {"@type": "xsd:integer"},
                    "owl:minCardinality": {"@type": "xsd:integer"}
                }
            ],
            "@graph": [
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": "My RO-Crate",
                    "description": "Generated RO-Crate with schema and data",
                    "hasPart": [
                        {
                            "@id": "data.csv"
                        }
                    ]
                },
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"}
                },
                {
                    "@id": "Person",
                    "@type": "rdfs:Class",
                    "rdfs:label": "Person",
                    "rdfs:comment": "Represents a person",
                    "rdfs:subClassOf": {"@id": "https://schema.org/Thing"},
                    "owl:restriction": [{"@id": "Person_name_restriction"}]
                },
                {
                    "@id": "name",
                    "@type": "rdf:Property", 
                    "rdfs:label": "Name",
                    "schema:domainIncludes": {"@id": "Person"},
                    "schema:rangeIncludes": {"@id": "http://www.w3.org/2001/XMLSchema#string"}
                },
                {
                    "@id": "Person_name_restriction",
                    "@type": "owl:Restriction",
                    "owl:onProperty": {"@id": "name"},
                    "owl:minCardinality": 1
                },
                {
                    "@id": "person1",
                    "@type": "Person",
                    "name": "Alice Johnson",
                    "email": "alice@example.com"
                },
                {
                    "@id": "data.csv",
                    "@type": "File",
                    "name": "Experimental Data",
                    "encodingFormat": "text/csv"
                }
            ]
        }
    """

    _forward_ref_resolver: ForwardRefResolver = PrivateAttr(
        default_factory=ForwardRefResolver
    )
    types: list[Type] = Field(default_factory=list)
    property_types: list[TypeProperty] = Field(default_factory=list)  # Standalone properties not attached to types
    restrictions: list[Restriction] = Field(default_factory=list)  # Standalone restrictions 
    metadata_entries: list[MetadataEntry] = Field(default_factory=list)
    files: list[dict] = Field(default_factory=list)  # Store file info for later inclusion
    prefix: str = "base"

    def model_post_init(self, context: Any) -> None:
        """
        Register all classes, properties, and restrictions for later reference resolution.
        Convert all string refs in properties to ForwardRef using Pydantic post-init.
        """
        for current_type in self.types:
            self._forward_ref_resolver.register(current_type.id, current_type)
            if current_type.rdfs_property:
                for prop in current_type.rdfs_property:
                    self._forward_ref_resolver.register(prop.id, prop)
                    
        # Register standalone properties
        for prop in self.property_types:
            self._forward_ref_resolver.register(prop.id, prop)
            
        # Register standalone restrictions
        for restriction in self.restrictions:
            self._forward_ref_resolver.register(restriction.id, restriction)
            
        super().model_post_init(context)

    def resolve_ref(self, ref):
        """
        Resolve a reference (ForwardRef, str, or id) to the actual object using the registry.
        """
        if isinstance(ref, ForwardRef):
            return self._forward_ref_resolver.resolve(ref.ref)
        elif isinstance(ref, str):
            return self._forward_ref_resolver.resolve(ref)
        else:
            return ref

    def resolve_forward_refs(self):
        """
        Walk all types/properties and delegate reference resolution to each property.
        """
        for current_type in self.types:
            current_type.resolve(self._forward_ref_resolver)
                
    # Fluent builder API methods
    def addType(self, type_obj: Type):
        """Add a type to the schema"""
        self.types.append(type_obj)
        self._forward_ref_resolver.register(type_obj.id, type_obj)
        if type_obj.rdfs_property:
            for prop in type_obj.rdfs_property:
                self._forward_ref_resolver.register(prop.id, prop)
        return self
        
    def _is_placeholder_id(self, entry_id: str) -> bool:
        """Check if an ID is a placeholder/dummy (automatically generated)"""
        # Placeholder IDs use explicit naming patterns to make them easy to identify
        import re
        
        # Check for explicit placeholder/dummy patterns
        placeholder_patterns = [
            r'.*_placeholder_.*',     # Contains "placeholder"
        ]
        
        for pattern in placeholder_patterns:
            if re.match(pattern, entry_id, re.IGNORECASE):
                return True
        

        # Check for hex patterns that are long (8+ chars)
        if re.search(r'[a-f0-9]{8,}', entry_id.lower()):
            return True
            
        return False
    
    def _entries_are_equivalent(self, entry1: MetadataEntry, entry2: MetadataEntry) -> bool:
        """Check if two metadata entries represent the same conceptual entity"""
        # Must have same class
        if entry1.class_id != entry2.class_id:
            return False
            
        # Compare properties (excluding None values and 'id' field since ID is stored separately)
        props1 = {k: v for k, v in entry1.properties.items() if v is not None and k != 'id'}
        props2 = {k: v for k, v in entry2.properties.items() if v is not None and k != 'id'}
        
        if props1 != props2:
            return False
            
        # For placeholder resolution, we're more lenient with references
        # If one entry is a placeholder, we only compare non-empty reference lists
        # This handles circular references where placeholders might have incomplete refs
        is_placeholder1 = self._is_placeholder_id(entry1.id)
        is_placeholder2 = self._is_placeholder_id(entry2.id)
        
        if is_placeholder1 or is_placeholder2:
            # For placeholder comparisons, be more flexible with references
            # Placeholders may have incomplete reference sets due to circular dependency resolution
            refs1 = {k: sorted(v) for k, v in entry1.references.items() if v}
            refs2 = {k: sorted(v) for k, v in entry2.references.items() if v}
            
            if not refs1 and not refs2:
                return True  # Both have no references
            elif not refs1 or not refs2:
                # One has references, one doesn't - could be placeholder vs real
                return True
            else:
                # Both have references - for placeholders, check if one is a subset of the other
                # This handles cases where the placeholder has fewer refs due to circular resolution
                smaller_refs = refs1 if len(refs1) <= len(refs2) else refs2
                larger_refs = refs2 if len(refs1) <= len(refs2) else refs1
                
                # Check if all references in the smaller set exist in the larger set with same values
                for key, values in smaller_refs.items():
                    if key not in larger_refs or larger_refs[key] != values:
                        return False
                return True
        else:
            # Both are real entries, require exact reference match
            refs1 = {k: sorted(v) for k, v in entry1.references.items() if v}
            refs2 = {k: sorted(v) for k, v in entry2.references.items() if v}
            return refs1 == refs2
    
    def _choose_preferred_entry(self, entry1: MetadataEntry, entry2: MetadataEntry) -> MetadataEntry:
        """Choose the preferred entry when duplicates are found"""
        # Prefer entry with real ID over placeholder/dummy ID
        placeholder1 = self._is_placeholder_id(entry1.id)
        placeholder2 = self._is_placeholder_id(entry2.id)
        
        if placeholder1 and not placeholder2:
            return entry2
        elif not placeholder1 and placeholder2:
            return entry1
        else:
            # Both are placeholder or both are real, prefer the shorter ID (more likely to be user-defined)
            if len(entry1.id) <= len(entry2.id):
                return entry1
            else:
                return entry2

    def addEntry(self, entry: MetadataEntry):
        """Add a metadata entry to the schema, checking for and removing duplicates"""
        # Check if this entry is equivalent to any existing entry
        for i, existing_entry in enumerate(self.metadata_entries):
            if self._entries_are_equivalent(entry, existing_entry):
                # Found equivalent entry, check if one is a placeholder
                placeholder1 = self._is_placeholder_id(entry.id)
                placeholder2 = self._is_placeholder_id(existing_entry.id)

                if placeholder1:
                    # Keep existing entry, don't add new one 
                    self._update_references(entry.id, existing_entry.id)
                    return self
                elif not placeholder1 and placeholder2:
                    # Replace existing with new entry
                    removed_id = existing_entry.id
                    self.metadata_entries[i] = entry
                    # Update all references to point to the new entry ID
                    self._update_references(removed_id, entry.id)
                    return self
                
                # Both are real continue
        
        # No duplicates found, add the new entry
        self.metadata_entries.append(entry)
        return self
    
    def resolve_placeholders(self):
        """
        Resolve placeholder entities by finding and merging them with real entities.
        This should be called after all model instances have been added to handle
        circular references that create placeholder duplicates.
        """
        placeholders_to_remove = []
        updates = {}  # mapping of old_id -> new_id
        
        # Find all placeholder entries
        placeholder_entries = [entry for entry in self.metadata_entries if self._is_placeholder_id(entry.id)]
        real_entries = [entry for entry in self.metadata_entries if not self._is_placeholder_id(entry.id)]
        
        for placeholder in placeholder_entries:
            # Look for a real entry with equivalent content
            matching_real_entry = None
            for real_entry in real_entries:
                if self._entries_are_equivalent(placeholder, real_entry):
                    matching_real_entry = real_entry
                    break
            
            if matching_real_entry:
                # Found a match, mark placeholder for removal and track the ID mapping
                placeholders_to_remove.append(placeholder)
                updates[placeholder.id] = matching_real_entry.id
                print(f"🔄 Resolving placeholder {placeholder.id} -> {matching_real_entry.id}")
        
        # Remove placeholder entries
        for placeholder in placeholders_to_remove:
            self.metadata_entries.remove(placeholder)
        
        # Update all references from placeholder IDs to real IDs
        for old_id, new_id in updates.items():
            self._update_references(old_id, new_id)
        
        if placeholders_to_remove:
            print(f"🔄 Resolved {len(placeholders_to_remove)} placeholder(s) to avoid circular import duplicates")
        return self
    
    def _find_equivalent_entry_for_model(self, model_instance: BaseModel) -> Optional[MetadataEntry]:
        """
        Find an existing metadata entry that represents the same Pydantic model instance.
        
        This is used to avoid creating duplicate entries when processing object references.
        """
        # Convert the model instance to a temporary metadata entry for comparison
        model_class = type(model_instance)
        model_name = model_class.__name__
        
        # Extract properties from instance
        temp_properties = {}
        for field_name in model_class.model_fields.keys():
            field_value = getattr(model_instance, field_name, None)
            if field_value is None or isinstance(field_value, BaseModel) or isinstance(field_value, list):
                continue  # Skip references and None values for comparison
            if isinstance(field_value, datetime):
                temp_properties[field_name] = field_value.isoformat()
            else:
                temp_properties[field_name] = field_value
        
        # Find an existing entry with the same class and properties
        for existing_entry in self.metadata_entries:
            if (existing_entry.class_id == model_name and 
                existing_entry.properties == temp_properties):
                return existing_entry
        
        return None
    
    def _update_references(self, old_id: str, new_id: str):
        """
        Update all references in metadata entries from old_id to new_id.
        
        This is used when removing duplicate entries to ensure all references
        point to the kept entry rather than the removed one.
        """
        for entry in self.metadata_entries:
            # Update references in all reference lists
            for ref_name, ref_list in entry.references.items():
                if ref_list:  # Only process non-empty lists
                    updated_refs = [new_id if ref_id == old_id else ref_id for ref_id in ref_list]
                    entry.references[ref_name] = updated_refs
    
    def add_file(self, file_path: Union[str, Path], name: Optional[str] = None, 
                description: Optional[str] = None, **properties) -> 'SchemaFacade':
        """
        Add a file to be included in the RO-Crate when written.
        
        This method stores file information that will be used when write() is called.
        The actual file copying and File entity creation happens during write().
        
        Args:
            file_path: Path to the file to include
            name: Human-readable name for the file (defaults to filename)
            description: Description of the file's content/purpose
            **properties: Additional properties for the File entity
            
        Returns:
            Self for method chaining
            
        Example:
            facade.add_file("data.csv", name="Experimental Results", 
                           description="Raw measurement data from synthesis experiment")
        """
        file_path = Path(file_path)
        
        if not name:
            name = file_path.stem.replace('_', ' ').replace('-', ' ').title()
            
        if not description:
            description = f"Data file: {file_path.name}"
        
        file_info = {
            'path': file_path,
            'name': name,
            'description': description,
            'properties': properties
        }
        
        self.files.append(file_info)
        return self
    
    def get_files(self) -> list[dict]:
        """Get list of files to be included in the crate"""
        return self.files
    
    def clear_files(self) -> 'SchemaFacade':
        """Remove all file references from the facade"""
        self.files.clear()
        return self
    
    @classmethod
    def from_ro_crate(cls, path: Union[str, Path, ROCrate]) -> 'SchemaFacade':
        """
        Import SchemaFacade from RO-Crate. This can be the folder or the metadata file itself.
        
        Args:
            path: Path to RO-Crate folder or ro-crate-metadata.json file
            
        Returns:
            SchemaFacade with imported types, properties, restrictions and metadata entries
        """
        import json
        from pathlib import Path

        if isinstance(path, ROCrate):
            crate_data = path.metadata
            return cls.from_dict(crate_data)

        path = Path(path)
        # Search for file called ro-crate-metadata.json

        if path.is_dir():
            path = path / "ro-crate-metadata.json"
        if not path.is_file():
            # Search in subfolders
            for subpath in path.glob("**/ro-crate-metadata.json"):
                if subpath.is_file():
                    path = subpath
                    break
        if not path.is_file():
            raise FileNotFoundError(f"Could not find ro-crate-metadata.json in {path}")
        with open(path, 'r', encoding='utf-8') as f:
            crate_data = json.load(f)
            
        return cls.from_dict(crate_data)
    
    @classmethod  
    def from_dict(cls, crate_data: dict) -> 'SchemaFacade':
        """
        Import SchemaFacade from RO-Crate dictionary.
        
        Follows the proper import flow:
        1. Parse rdfs:Class entities → create Type objects
        2. Parse rdf:Property entities → create TypeProperty objects  
        3. Parse owl:Restriction entities → create Restriction objects
        4. Link properties to types based on owl:restriction references
        5. Parse remaining entities → create MetadataEntry objects
        
        Args:
            crate_data: Dictionary containing RO-Crate JSON-LD data
            
        Returns:
            SchemaFacade with imported schema and data
        """
        graph = crate_data.get("@graph", [])
        context = crate_data.get("@context", [])
        
        # Parse and process the JSON-LD context
        context_processor = cls._parse_jsonld_context(context)
        
        # Step 1: Parse all schema elements first
        parsed_classes = {}      # id -> raw_data
        parsed_properties = {}   # id -> raw_data  
        parsed_restrictions = {} # id -> raw_data
        metadata_items = []      # remaining non-schema items
        
        # Separate schema elements from metadata
        for item in graph:
            item_type = item.get("@type")
            item_id = item.get("@id", "")
            
            # Expand URIs using context for proper type detection
            expanded_type = cls._expand_uri_with_context(item_type, context_processor) if item_type else ""
            expanded_id = cls._expand_uri_with_context(item_id, context_processor) if item_id else ""
            
            # Check for rdfs:Class (could be prefixed or full URI)
            if (item_type == "rdfs:Class" or 
                expanded_type.endswith("/Class") or 
                expanded_type.endswith("#Class")):
                parsed_classes[item_id] = item
            # Check for rdf:Property or rdfs:Property
            elif (item_type in ["rdf:Property", "rdfs:Property"] or
                  expanded_type.endswith("/Property") or
                  expanded_type.endswith("#Property")):
                parsed_properties[item_id] = item
            # Check for owl:Restriction
            elif (item_type in ["owl:Restriction", "owl:restriction"] or
                  expanded_type.endswith("/Restriction") or
                  expanded_type.endswith("#Restriction")):
                parsed_restrictions[item_id] = item
            elif item_id not in ["./", "ro-crate-metadata.json"]:  # Skip RO-Crate structure
                metadata_items.append(item)
        
        # Step 2: Create TypeProperty objects
        type_properties = {}
        for prop_id, prop_data in parsed_properties.items():
            local_id = cls._extract_local_id(prop_id)
            
            # Extract ontology mapping from owl:equivalentProperty
            ontology = None
            equiv_prop = prop_data.get("owl:equivalentProperty", {})
            if isinstance(equiv_prop, dict):
                ontology = equiv_prop.get("@id")
            elif isinstance(equiv_prop, str):
                ontology = equiv_prop
            
            # Extract domain includes (what classes can have this property)
            domain_includes = []
            domain_data = prop_data.get("schema:domainIncludes", [])
            if isinstance(domain_data, dict):
                ref_id = domain_data.get("@id", "")
                if ref_id:
                    domain_includes = [cls._expand_uri_with_context(ref_id, context_processor)]
            elif isinstance(domain_data, list):
                for item in domain_data:
                    if isinstance(item, dict):
                        ref_id = item.get("@id", "")
                        if ref_id:
                            domain_includes.append(cls._expand_uri_with_context(ref_id, context_processor))
                    elif isinstance(item, str):
                        domain_includes.append(cls._expand_uri_with_context(item, context_processor))
            elif isinstance(domain_data, str):
                domain_includes = [cls._expand_uri_with_context(domain_data, context_processor)]
            
            # Extract range includes (what types this property can hold)
            range_includes = []
            range_data = prop_data.get("schema:rangeIncludes", [])
            if isinstance(range_data, dict):
                ref_id = range_data.get("@id", "")
                if ref_id:
                    range_includes = [cls._expand_uri_with_context(ref_id, context_processor)]
            elif isinstance(range_data, list):
                for item in range_data:
                    if isinstance(item, dict):
                        ref_id = item.get("@id", "")
                        if ref_id:
                            range_includes.append(cls._expand_uri_with_context(ref_id, context_processor))
                    elif isinstance(item, str):
                        range_includes.append(cls._expand_uri_with_context(item, context_processor))
            elif isinstance(range_data, str):
                range_includes = [cls._expand_uri_with_context(range_data, context_processor)]
            
            type_prop = TypeProperty(
                id=local_id,
                label=prop_data.get("rdfs:label"),
                comment=prop_data.get("rdfs:comment"), 
                domain_includes=domain_includes,
                range_includes=range_includes,
                ontological_annotations=[ontology] if ontology else None
            )
            type_properties[prop_id] = type_prop
        
        # Step 3: Create Restriction objects  
        restrictions = {}
        for restr_id, restr_data in parsed_restrictions.items():
            on_property = restr_data.get("owl:onProperty", {})
            prop_id = on_property.get("@id") if isinstance(on_property, dict) else on_property
            
            restriction = Restriction(
                id=cls._extract_local_id(restr_id),
                property_type=cls._extract_local_id(prop_id) if prop_id else "",
                min_cardinality=restr_data.get("owl:minCardinality"),
                max_cardinality=restr_data.get("owl:maxCardinality")
            )
            restrictions[restr_id] = restriction
        
        # Step 4: Create Type objects and link properties via restrictions
        types = []
        linked_property_ids = set()  # Track which properties we've linked across all types
        
        for class_id, class_data in parsed_classes.items():
            local_id = cls._extract_local_id(class_id)
            
            # Extract subclass relationships
            subclass_of = ["https://schema.org/Thing"]  # Default
            subclass_data = class_data.get("rdfs:subClassOf", {})
            if isinstance(subclass_data, dict):
                subclass_ref = subclass_data.get("@id")
                if subclass_ref:
                    subclass_of = [subclass_ref]
            elif isinstance(subclass_data, str):
                subclass_of = [subclass_data]
            
            # Extract ontology mapping from owl:equivalentClass
            ontology = None
            equiv_class = class_data.get("owl:equivalentClass", {})
            if isinstance(equiv_class, dict):
                ontology = equiv_class.get("@id")
            elif isinstance(equiv_class, str):
                ontology = equiv_class
            
            # Get restrictions linked to this class and their properties
            class_restrictions = []
            class_properties = []
            
            # First, link properties via owl:restriction (preferred method)
            restr_refs = class_data.get("owl:restriction", [])
            if isinstance(restr_refs, dict):
                restr_refs = [restr_refs]
            
            for restr_ref in restr_refs:
                restr_id = restr_ref.get("@id") if isinstance(restr_ref, dict) else restr_ref
                if restr_id in restrictions:
                    restriction = restrictions[restr_id]
                    class_restrictions.append(restriction)
                    
                    # Find the corresponding property and add it to the class
                    for prop_id, type_prop in type_properties.items():
                        if type_prop.id == restriction.property_type:
                            # Set required based on restriction cardinality
                            prop_copy = type_prop.model_copy()
                            prop_copy.required = (restriction.min_cardinality or 0) > 0
                            class_properties.append(prop_copy)
                            linked_property_ids.add(prop_id)
                            break
            
            # Fallback: Link properties via schema:domainIncludes if not linked via restrictions
            for prop_id, type_prop in type_properties.items():
                if prop_id not in linked_property_ids:
                    # Check if this property references this class in its domain
                    for domain_ref in type_prop.domain_includes:
                        domain_class_id = cls._extract_local_id(domain_ref) if domain_ref else ""
                        if domain_class_id == local_id:
                            # Property belongs to this class - add it
                            prop_copy = type_prop.model_copy()
                            prop_copy.required = False  # Default to optional when no restriction
                            class_properties.append(prop_copy)
                            linked_property_ids.add(prop_id)
                            break
            
            # Create Type object
            ro_type = Type(
                id=local_id,
                subclass_of=subclass_of,
                ontological_annotations=[ontology] if ontology else None,
                rdfs_property=class_properties,
                comment=class_data.get("rdfs:comment"),
                label=class_data.get("rdfs:label"),
                restrictions=class_restrictions
            )
            types.append(ro_type)
        
        # Step 5: Create MetadataEntry objects from remaining items
        metadata_entries = []
        for item in metadata_items:
            item_type = item.get("@type", "")
            item_id = item.get("@id", "")
            
            # Extract local class name
            local_class = cls._extract_local_id(item_type) if item_type else "Unknown"
            local_id = cls._extract_local_id(item_id)
            
            # Extract property values (exclude @id, @type)
            properties = {}
            references = {}
            
            for key, value in item.items():
                if key not in ["@id", "@type"]:
                    local_key = cls._extract_local_id(key)
                    
                    # Use context to determine if this should be treated as a reference
                    is_reference_property = cls._is_reference_property(key, context_processor)
                    
                    if isinstance(value, dict) and "@id" in value:
                        # Explicit reference to another entity - wrap in list as expected by MetadataEntry
                        references[local_key] = [cls._extract_local_id(value["@id"])]
                    elif isinstance(value, list):
                        # Handle arrays - could be references or literals
                        ref_values = []
                        literal_values = []
                        
                        for item_val in value:
                            if isinstance(item_val, dict) and "@id" in item_val:
                                ref_values.append(cls._extract_local_id(item_val["@id"]))
                            elif is_reference_property and isinstance(item_val, str):
                                # Context indicates this should be treated as reference
                                ref_values.append(cls._extract_local_id(item_val))
                            else:
                                literal_values.append(item_val)
                        
                        # Store in appropriate category
                        if ref_values:
                            references[local_key] = ref_values
                        if literal_values:
                            properties[local_key] = literal_values if len(literal_values) > 1 else literal_values[0]
                    elif is_reference_property and isinstance(value, str):
                        # Context indicates this string should be treated as a reference
                        references[local_key] = [cls._extract_local_id(value)]
                    else:
                        # Direct property value
                        properties[local_key] = value
            
            entry = MetadataEntry(
                id=local_id,
                class_id=local_class,
                properties=properties,
                references=references
            )
            metadata_entries.append(entry)
        
        # Step 6: Identify standalone properties and restrictions
        # Properties that aren't linked to any type via restrictions or domainIncludes
        standalone_properties = []
        standalone_restrictions = []
        
        for prop_id, type_prop in type_properties.items():
            # Check if this property is linked to any type
            is_linked = prop_id in linked_property_ids
            if not is_linked:
                standalone_properties.append(type_prop)
        
        # Restrictions that aren't referenced by any type
        used_restriction_ids = set()
        for type_obj in types:
            if type_obj.restrictions:
                for restriction in type_obj.restrictions:
                    used_restriction_ids.add(restriction.id)
        
        for restr_id, restriction in restrictions.items():
            if restriction.id not in used_restriction_ids:
                standalone_restrictions.append(restriction)

        # Create and return SchemaFacade with all components
        return cls(
            types=types,
            property_types=standalone_properties,
            restrictions=standalone_restrictions,
            metadata_entries=metadata_entries
        )
    
    @staticmethod
    def _parse_jsonld_context(context) -> dict:
        """
        Parse JSON-LD context to extract namespace mappings and property configurations.
        
        Args:
            context: JSON-LD @context (string, dict, or list)
            
        Returns:
            Dictionary with namespace mappings and property type information
        """
        context_info = {
            'namespaces': {},  # prefix -> URI mapping
            'property_types': {},  # property -> type info
            'base_uri': None
        }
        
        if isinstance(context, str):
            # Single context URL - we can't extract local mappings from this
            # but we know it's the base RO-Crate context
            return context_info
        elif isinstance(context, list):
            # Process each context in the list
            for ctx_item in context:
                if isinstance(ctx_item, str):
                    continue  # Skip URLs
                elif isinstance(ctx_item, dict):
                    context_info = SchemaFacade._merge_context_dict(context_info, ctx_item)
        elif isinstance(context, dict):
            # Single context object
            context_info = SchemaFacade._merge_context_dict(context_info, context)
        
        return context_info
    
    @staticmethod 
    def _merge_context_dict(context_info: dict, ctx_dict: dict) -> dict:
        """Merge a context dictionary into the context info"""
        for key, value in ctx_dict.items():
            if isinstance(value, str):
                # Simple namespace mapping: "base": "http://example.com/"
                context_info['namespaces'][key] = value
                # Check if this could be our base namespace
                if key in ['base', '@base'] or 'example.com' in value:
                    context_info['base_uri'] = value
            elif isinstance(value, dict):
                # Complex property definition: "name": {"@id": "schema:name", "@type": "@id"}
                context_info['property_types'][key] = value
        
        return context_info
    
    @staticmethod
    def _expand_uri_with_context(uri: str, context_info: dict) -> str:
        """
        Expand a prefixed URI using the context information.
        
        Args:
            uri: URI that may be prefixed (e.g., 'base:Person', 'schema:name')
            context_info: Parsed context information
            
        Returns:
            Expanded URI (e.g., 'http://example.com/Person', 'https://schema.org/name')
        """
        if not uri or ':' not in uri:
            return uri
            
        prefix, local_part = uri.split(':', 1)
        namespace_uri = context_info['namespaces'].get(prefix)
        
        if namespace_uri:
            # Ensure namespace URI ends properly for concatenation
            if not namespace_uri.endswith(('//', '/', '#')):
                namespace_uri += '/'
            return namespace_uri + local_part
        
        return uri  # Return unchanged if we can't expand it
    
    @staticmethod
    def _contract_uri_with_context(uri: str, context_info: dict) -> str:
        """
        Contract a full URI to a prefixed form using context information.
        
        Args:
            uri: Full URI (e.g., 'http://example.com/Person')
            context_info: Parsed context information
            
        Returns:
            Contracted URI if possible (e.g., 'base:Person'), otherwise original
        """
        if not uri:
            return uri
            
        # Check against known namespaces
        for prefix, namespace_uri in context_info['namespaces'].items():
            # Handle different namespace ending patterns
            if namespace_uri.endswith(('//', '/', '#')):
                base_ns = namespace_uri
            else:
                base_ns = namespace_uri + '/'
                
            if uri.startswith(base_ns):
                local_part = uri[len(base_ns):]
                return f"{prefix}:{local_part}"
        
        return uri
    
    @staticmethod
    def _is_reference_property(prop_name: str, context_info: dict) -> bool:
        """
        Check if a property should be treated as a reference (points to another entity).
        
        Args:
            prop_name: Property name
            context_info: Parsed context information
            
        Returns:
            True if property contains references to other entities
        """
        prop_config = context_info['property_types'].get(prop_name, {})
        return prop_config.get('@type') == '@id'
    
    @staticmethod
    def _extract_local_id(uri: str) -> str:
        """Extract local ID from URI (e.g., 'base:Person' → 'Person', 'http://example.com/Person' → 'Person')"""
        if not uri:
            return ""
        
        # Handle full URLs (http://, https://)
        if uri.startswith(('http://', 'https://')):
            return uri.split("/")[-1] if "/" in uri else uri
        
        # Handle namespace prefixes (base:Person, schema:name, etc.)
        if ":" in uri:
            return uri.split(":")[-1]
            
        # Handle simple paths or plain strings
        return uri.split("/")[-1] if "/" in uri else uri
    
    def write(self, destination: str, name: Optional[str] = None, description: Optional[str] = None, 
              license: Optional[str] = None, **kwargs):
        """
        Write the schema as an RO-Crate to the specified destination.
        Automatically includes any files that were added via add_file().
        Includes dynamic JSON-LD context based on actual vocabulary usage.
        
        Args:
            destination: Directory path where the crate should be written
            name: Name for the RO-Crate (optional)
            description: Description for the RO-Crate (optional)  
            license: License identifier for the RO-Crate (optional)
            **kwargs: Additional metadata for the RO-Crate
        """
        # Get the complete RO-Crate using get_crate (includes dynamic context)
        crate: ROCrate = self.get_crate(name=name, description=description, license=license, **kwargs)
        
        # Write to destination
        crate.write(destination)
        
        return self
    
    def get_dynamic_context(self) -> dict:
        """
        Generate and return the dynamic JSON-LD context based on the vocabularies 
        and properties actually used in this schema.
        
        Returns:
            JSON-LD @context that includes only the namespaces and properties
            that are actually used in the schema
        """
        from lib_ro_crate_schema.crate.jsonld_utils import get_context
        
        # Generate RDF graph and extract context
        graph = self.to_graph()
        return get_context(graph)
    
    def to_json(self) -> dict:
        """
        Convert the schema to JSON-LD format without writing to disk.
        
        Returns:
            JSON-LD representation of the schema as RO-Crate
        """
        from rocrate.rocrate import ROCrate
        from lib_ro_crate_schema.crate.jsonld_utils import add_schema_to_crate
        
        # Resolve any forward references first
        self.resolve_forward_refs()
        
        # Create temporary crate and get JSON representation
        crate = ROCrate()
        crate = add_schema_to_crate(self, crate)
        
        # Return the JSON representation of the crate
        with tempfile.TemporaryDirectory() as temp_dir:
            crate.write(temp_dir)
            metadata_file = Path(temp_dir) / "ro-crate-metadata.json"
            with open(metadata_file, 'r') as f:
                return json.load(f)

    def to_triples(self) -> Generator[Triple, None, None]:
        # Generate triples for types (includes their attached properties and restrictions)
        for p in self.types:
            yield from p.to_triples()
            
        # Generate triples for standalone properties
        for prop in self.property_types:
            yield from prop.to_triples()
            
        # Generate triples for standalone restrictions  
        for restriction in self.restrictions:
            yield from restriction.to_triples()
            
        # Generate triples for metadata entries
        for m in self.metadata_entries:
            yield from m.to_triples()

    def get_properties(self) -> Generator[TypeProperty, None, None]:
        # Get all properties - both standalone and attached to types
        all_properties = []
        
        # Add standalone properties
        all_properties.extend(self.property_types)
        
        # Add properties from types
        for current_type in self.types:
            if current_type.rdfs_property:
                all_properties.extend(current_type.rdfs_property)
        
        # Remove duplicates based on ID and yield
        seen_ids = set()
        for prop in all_properties:
            if prop.id not in seen_ids:
                seen_ids.add(prop.id)
                yield prop

    def getPropertyTypes(self) -> list[TypeProperty]:
        """Get list of standalone property types (not attached to any Type)"""
        return self.get_properties()
    


    def to_graph(self) -> Graph:
        """Convert the schema to an RDFLib Graph"""
        local_graph = Graph()
        [local_graph.add(triple) for triple in self.to_triples()]
        local_graph.bind(prefix=self.prefix, namespace=BASE)
        return local_graph
    
    # New methods for decorator integration
    
    def export_pydantic_model(self, type_id: str, base_class: Optional[TypingType[BaseModel]] = None) -> TypingType[BaseModel]:
        """
        Export a Type definition as a Pydantic model class with BFS dependency resolution.
        
        This method now uses the Registry's BFS traversal to ensure all dependencies
        are resolved in the correct order before creating the target model.
        
        Args:
            type_id: ID of the Type to export
            base_class: Optional base class to inherit from (defaults to BaseModel)
            
        Returns:
            Dynamically generated Pydantic model class
            
        Raises:
            ValueError: If type_id is not found in the schema
            
        Example:
            facade = SchemaFacade()
            # ... add types to facade ...
            PersonModel = facade.export_pydantic_model("Person")
            person = PersonModel(name="Alice", age=30)
        """
        # Check if already cached
        cached_model = self._forward_ref_resolver.get_pydantic_model(type_id)
        if cached_model:
            return cached_model
            
        # Find the Type definition
        type_def = self.get_type(type_id)
        if not type_def:
            raise ValueError(f"Type '{type_id}' not found in schema")
        
        # Use BFS to find all dependencies and export them first
        dependency_order = self._forward_ref_resolver.collect_dependencies_bfs(type_id)
        
        # Export all dependencies first (except the target)
        for dep_type_id in dependency_order[:-1]:  # Exclude the target type itself
            if not self._forward_ref_resolver.get_pydantic_model(dep_type_id):
                dep_model = self._create_single_pydantic_model(dep_type_id, base_class)
                self._forward_ref_resolver.register_pydantic_model(dep_type_id, dep_model)
        
        # Finally export the target model
        target_model = self._create_single_pydantic_model(type_id, base_class)
        self._forward_ref_resolver.register_pydantic_model(type_id, target_model)
        
        # Rebuild all models to resolve forward references
        self._rebuild_pydantic_models(dependency_order)
        
        return target_model
    
    def _create_single_pydantic_model(self, type_id: str, base_class: Optional[TypingType[BaseModel]] = None) -> TypingType[BaseModel]:
        """
        Create a single Pydantic model without dependency resolution.
        Used internally by the BFS-based export methods.
        """
        type_def = self.get_type(type_id)
        if not type_def:
            raise ValueError(f"Type '{type_id}' not found in schema")
        
        # Determine base class
        if base_class is None:
            base_class = BaseModel
        
        # Build field definitions from Type properties
        field_definitions = {}
        annotations = {}
        
        if type_def.rdfs_property:
            for prop in type_def.rdfs_property:
                field_name = prop.id
                
                # Determine Python type from range_includes with registry-aware resolution
                python_type = self._rdf_type_to_python_type_with_registry(prop.range_includes)
                
                # Check if field is required from restrictions
                is_required = self._is_field_required(type_def, field_name)
                is_list = self._is_field_list(type_def, field_name)
                
                # Adjust type for lists
                if is_list and python_type != Any:
                    from typing import List as TypingList
                    python_type = TypingList[python_type]
                
                # Create Field with metadata
                field_kwargs = {}
                if prop.comment:
                    field_kwargs['description'] = prop.comment
                if not is_required:
                    field_kwargs['default'] = None
                    python_type = Optional[python_type]
                
                if field_kwargs:
                    field_definitions[field_name] = Field(**field_kwargs)
                else:
                    field_definitions[field_name] = ... if is_required else None
                
                annotations[field_name] = python_type
        
        # Create the class dynamically
        class_name = type_def.id
        
        # Create class attributes dictionary
        class_dict = {
            '__annotations__': annotations,
            '__module__': f"__pydantic_export_{id(self)}",  # Unique module name
        }
        
        # Add field definitions
        class_dict.update(field_definitions)
        
        # Add docstring from Type comment
        if type_def.comment:
            class_dict['__doc__'] = type_def.comment
        
        # Create the class
        model_class = type(class_name, (base_class,), class_dict)
        
        return model_class
    
    def export_all_pydantic_models(self, base_class: Optional[TypingType[BaseModel]] = None) -> dict[str, TypingType[BaseModel]]:
        """
        Export all Types in the schema as Pydantic model classes with proper dependency resolution.
        
        This method uses the Registry's dependency resolution to export all models
        in the correct order, ensuring forward references work properly.
        
        Args:
            base_class: Optional base class for all models (defaults to BaseModel)
            
        Returns:
            Dictionary mapping type IDs to generated Pydantic model classes
            
        Example:
            facade = SchemaFacade()
            # ... add types to facade ...
            models = facade.export_all_pydantic_models()
            PersonModel = models["Person"]
            OrganizationModel = models["Organization"]
        """
        models = {}
        
        # Get all type IDs
        type_ids = [type_def.id for type_def in self.types]
        
        # Use registry to get proper dependency order for all types
        ordered_type_ids = self._forward_ref_resolver.get_all_dependencies(type_ids)
        
        # Export models in dependency order
        for type_id in ordered_type_ids:
            if not self._forward_ref_resolver.get_pydantic_model(type_id):
                model_class = self._create_single_pydantic_model(type_id, base_class)
                self._forward_ref_resolver.register_pydantic_model(type_id, model_class)
                models[type_id] = model_class
            else:
                models[type_id] = self._forward_ref_resolver.get_pydantic_model(type_id)
        
        # Rebuild all models to resolve forward references
        self._rebuild_pydantic_models(ordered_type_ids)
        
        return models
    
    def clear_pydantic_model_cache(self):
        """Clear the cached Pydantic models to force regeneration"""
        if hasattr(self._forward_ref_resolver, '_pydantic_models'):
            self._forward_ref_resolver._pydantic_models.clear()
    
    def _rdf_type_to_python_type(self, range_includes: List[str]) -> TypingType:
        """Convert RDF range types to Python types (legacy method)"""
        return self._rdf_type_to_python_type_with_registry(range_includes)
    
    def _rdf_type_to_python_type_with_registry(self, range_includes: List[str]) -> TypingType:
        """Convert RDF range types to Python types with Registry-aware resolution"""
        if not range_includes:
            return Any
        
        # Take the first range type for simplicity
        rdf_type = range_includes[0]
        
        # Map common XSD types to Python types
        type_mapping = {
            'http://www.w3.org/2001/XMLSchema#string': str,
            'http://www.w3.org/2001/XMLSchema#integer': int,
            'http://www.w3.org/2001/XMLSchema#int': int,
            'http://www.w3.org/2001/XMLSchema#long': int,
            'http://www.w3.org/2001/XMLSchema#float': float,
            'http://www.w3.org/2001/XMLSchema#double': float,
            'http://www.w3.org/2001/XMLSchema#decimal': float,
            'http://www.w3.org/2001/XMLSchema#boolean': bool,
            'http://www.w3.org/2001/XMLSchema#date': str,  # Could use datetime.date
            'http://www.w3.org/2001/XMLSchema#dateTime': str,  # Could use datetime.datetime
            'http://www.w3.org/2001/XMLSchema#time': str,  # Could use datetime.time
            'http://www.w3.org/2001/XMLSchema#anyURI': str,
            'https://schema.org/Text': str,
            'https://schema.org/Number': float,
            'https://schema.org/Integer': int,
            'https://schema.org/Boolean': bool,
            'https://schema.org/URL': str,
            'https://schema.org/Date': str,
            'https://schema.org/DateTime': str,
        }
        
        # Check if it's a known XSD/schema.org type
        if rdf_type in type_mapping:
            return type_mapping[rdf_type]
        
        # Check if it's a reference to another Type in our schema
        referenced_type = self.get_type(rdf_type)
        if referenced_type:
            # Check if we already have a Pydantic model for this type
            cached_model = self._forward_ref_resolver.get_pydantic_model(rdf_type)
            if cached_model:
                return cached_model
            # Return a forward reference string that Pydantic can resolve
            return f"'{rdf_type}'"
        
        # Extract local name for custom types
        local_name = self._extract_local_id(rdf_type)
        if self.get_type(local_name):
            # Check registry cache first
            cached_model = self._forward_ref_resolver.get_pydantic_model(local_name)
            if cached_model:
                return cached_model
            return f"'{local_name}'"
        
        # Default to Any for unknown types
        return Any
    
    def _rebuild_pydantic_models(self, type_ids: List[str]):
        """Rebuild all Pydantic models to resolve forward references"""
        import sys
        from types import ModuleType
        
        # Create a temporary module with all models for proper resolution
        temp_module_name = f"__pydantic_rebuild_{id(self)}"
        temp_module = ModuleType(temp_module_name)
        
        try:
            # Add all models to the temporary module namespace
            for type_id in type_ids:
                model_class = self._forward_ref_resolver.get_pydantic_model(type_id)
                if model_class:
                    setattr(temp_module, type_id, model_class)
                    # Update the model's module reference
                    model_class.__module__ = temp_module_name
            
            # Register the module
            sys.modules[temp_module_name] = temp_module
            
            # Rebuild all models
            for type_id in type_ids:
                model_class = self._forward_ref_resolver.get_pydantic_model(type_id)
                if model_class:
                    try:
                        model_class.model_rebuild()
                    except Exception as e:
                        print(f"Warning: Could not rebuild model {model_class.__name__}: {e}")
        
        finally:
            # Clean up the temporary module
            if temp_module_name in sys.modules:
                del sys.modules[temp_module_name]
    
    def _is_field_required(self, type_def: Type, field_name: str) -> bool:
        """Check if a field is required based on OWL restrictions"""
        if not type_def.restrictions:
            return False
        
        for restriction in type_def.restrictions:
            if restriction.property_type == field_name:
                return (restriction.min_cardinality or 0) > 0
        
        return False
    
    def _is_field_list(self, type_def: Type, field_name: str) -> bool:
        """Check if a field should be a list based on OWL restrictions"""
        if not type_def.restrictions:
            return False
        
        for restriction in type_def.restrictions:
            if restriction.property_type == field_name:
                # If max_cardinality is None (unbounded) or > 1, it's a list
                return restriction.max_cardinality is None or (restriction.max_cardinality or 0) > 1
        
        return False
    
    def add_pydantic_model(self, model_class: TypingType[BaseModel], 
                          ontology: Optional[str] = None,
                          comment: Optional[str] = None) -> Type:
        """
        Add a Pydantic model to the schema, either by using existing registration
        or by registering it on-the-fly.
        
        Args:
            model_class: The Pydantic model class
            ontology: Optional ontology URI (overrides decorator setting)  
            comment: Optional comment (overrides decorator setting)
            
        Returns:
            The generated Type object
        """
        # Check if model is already registered
        schema_registry = get_schema_registry()
        type_template = schema_registry.get_type_template(model_class.__name__)
        
        if not type_template:
            # Register the model if not already registered  
            # Use class name as default type_id for dynamic registration
            type_template = schema_registry.register_type_from_model(
                model_class=model_class,
                type_id=model_class.__name__,  # Default to class name
                ontology=ontology,
                comment=comment
            )
        
        # Convert to Type object and add to facade
        ro_crate_type = self._type_template_to_type(type_template)
        
            # Check if already exists in types
        existing_type = next((t for t in self.types if t.id == ro_crate_type.id), None)
        if not existing_type:
            self.types.append(ro_crate_type)
            self._forward_ref_resolver.register(ro_crate_type.id, ro_crate_type)
            
            # Register properties too
            if ro_crate_type.rdfs_property:
                for prop in ro_crate_type.rdfs_property:
                    self._forward_ref_resolver.register(prop.id, prop)
        
        return ro_crate_type
    
    def add_registered_models(self, *model_names: str) -> List[Type]:
        """
        Add models that were previously registered via @ro_crate_schema decorator.
        
        Args:
            *model_names: Names of registered models to add
            
        Returns:
            List of generated Type objects
        """
        schema_registry = get_schema_registry()
        added_types = []
        
        for model_name in model_names:
            type_template = schema_registry.get_type_template(model_name)
            if not type_template:
                raise ValueError(f"Model '{model_name}' is not registered. Use @ro_crate_schema decorator first.")
            
            ro_crate_type = self._type_template_to_type(type_template)
            
            # Check if already exists
            existing_type = next((t for t in self.types if t.id == ro_crate_type.id), None)
            if not existing_type:
                self.types.append(ro_crate_type)
                self._forward_ref_resolver.register(ro_crate_type.id, ro_crate_type)
                
                # Register properties
                if ro_crate_type.rdfs_property:
                    for prop in ro_crate_type.rdfs_property:
                        self._forward_ref_resolver.register(prop.id, prop)
                
                added_types.append(ro_crate_type)
        
        return added_types
    
    def add_all_registered_models(self) -> List[Type]:
        """
        Add all models that were registered via @ro_crate_schema decorator.
        
        Returns:
            List of generated Type objects
        """
        schema_registry = get_schema_registry()
        all_type_templates = schema_registry.get_all_type_templates()
        return self.add_registered_models(*all_type_templates.keys())
    
    def add_model_instance(self, instance: BaseModel, instance_id: Optional[str] = None) -> MetadataEntry:
        """
        Add a Pydantic model instance as a metadata entry.
        The model class should be registered first.
        
        Args:
            instance: Pydantic model instance
            instance_id: Optional custom ID for the instance
            
        Returns:
            The created MetadataEntry
        """
        model_class = type(instance)
        
        # Ensure the model type is in the schema
        self.add_pydantic_model(model_class)
        
        # Get the correct type ID from the schema registry (might be different from class name)
        schema_registry = get_schema_registry()
        
        # First try to get by explicit ID if the model was decorated
        if hasattr(model_class, '_ro_crate_id'):
            type_id = model_class._ro_crate_id
        else:
            # Fallback to class name for dynamic models
            type_id = model_class.__name__
            
        # Verify the type exists in our schema 
        type_template = schema_registry.get_type_template(type_id)
        if not type_template:
            # Try class name as fallback
            type_template = schema_registry.get_type_template(model_class.__name__)
            if type_template:
                type_id = type_template.id
        
        # Determine instance ID
        if instance_id is None:
            # Try to extract ID from instance if it has an @id or id field
            # Use getattr to access the actual field values, not model_dump()
            if hasattr(instance, '@id') and getattr(instance, '@id') is not None:
                instance_id = getattr(instance, '@id')
            elif hasattr(instance, 'id') and getattr(instance, 'id') is not None:
                instance_id = getattr(instance, 'id')
            else:
                # Generate placeholder ID as fallback
                instance_id = f"{type_id.lower()}_placeholder_{abs(hash(str(instance)))}"
        
        # Extract properties and references from instance
        properties = {}
        references = {}
        
        # Iterate over actual field values, not model_dump() output
        for field_name in type(instance).model_fields.keys():
            field_value = getattr(instance, field_name, None)
            
            if field_value is None:
                continue
            

            if isinstance(field_value, BaseModel):
                # Reference to another model instance
                # First, try to find an existing equivalent entry
                ref_instance_id = None
                
                # Check for explicit ID first
                if hasattr(field_value, '@id') and getattr(field_value, '@id') is not None:
                    ref_instance_id = getattr(field_value, '@id')
                elif hasattr(field_value, 'id') and getattr(field_value, 'id') is not None:
                    ref_instance_id = getattr(field_value, 'id')
                else:
                    # Check if an equivalent entry already exists in metadata
                    existing_entry = self._find_equivalent_entry_for_model(field_value)
                    if existing_entry:
                        ref_instance_id = existing_entry.id
                    else:
                        ref_instance_id = f"{type(field_value).__name__.lower()}_placeholder_{abs(hash(str(field_value)))}"
                    
                references[field_name] = [ref_instance_id]
                
                # Only recursively add if we don't already have an equivalent entry
                if not self._find_equivalent_entry_for_model(field_value):
                    self.add_model_instance(field_value, ref_instance_id)
            elif isinstance(field_value, list):
                # Handle lists (could be references or properties)
                field_refs = []
                for item in field_value:
                    if isinstance(item, BaseModel):
                        # Create proper ID for list item
                        ref_instance_id = None
                        
                        # Check for explicit ID first
                        if hasattr(item, '@id') and getattr(item, '@id') is not None:
                            ref_instance_id = getattr(item, '@id')
                        elif hasattr(item, 'id') and getattr(item, 'id') is not None:
                            ref_instance_id = getattr(item, 'id')
                        else:
                            # Check if an equivalent entry already exists in metadata
                            existing_entry = self._find_equivalent_entry_for_model(item)
                            if existing_entry:
                                ref_instance_id = existing_entry.id
                            else:
                                ref_instance_id = f"{type(item).__name__.lower()}_placeholder_{abs(hash(str(item)))}"
                            
                        field_refs.append(ref_instance_id)
                        
                        # Only recursively add if we don't already have an equivalent entry
                        if not self._find_equivalent_entry_for_model(item):
                            self.add_model_instance(item, ref_instance_id)
                    else:
                        # Simple value in list - not supported in current format
                        pass
                if field_refs:
                    references[field_name] = field_refs
            else:
                # Simple value - handle datetime serialization properly  
                if isinstance(field_value, datetime):
                    properties[field_name] = field_value.isoformat()
                else:
                    properties[field_name] = field_value
        
        # Create metadata entry
        entry = MetadataEntry(
            id=instance_id,
            class_id=type_id,  # Use the correct type ID
            properties=properties,
            references=references
        )
        
        # Use the same duplicate detection logic as addEntry
        self.addEntry(entry)

        # Return the entry that was actually kept (might be different if duplicate was found)
        final_entry = next((e for e in self.metadata_entries if 
                          self._entries_are_equivalent(e, entry) and self._is_placeholder_id(entry.id)), entry)
        return final_entry
    
    def _type_template_to_type(self, type_template: TypeTemplate) -> Type:
        """Convert TypeTemplate to Type object"""
        # Convert properties
        properties = []
        restrictions = []
        
        for prop_template in type_template.type_properties:
            # Create TypeProperty
            type_property = TypeProperty(
                id=prop_template.name,
                range_includes=[prop_template.rdf_type],
                domain_includes=[type_template.id],  # Use id instead of name
                ontological_annotations=[prop_template.ontology] if prop_template.ontology else [],
                comment=prop_template.comment,
                label=prop_template.name.replace('_', ' ').title()
            )
            properties.append(type_property)
            
            # Create OWL restrictions for all fields (conforming to Java architecture)
            if prop_template.required:
                # Required fields get minCardinality: 1
                # Lists get maxCardinality: None (unbounded), single values get maxCardinality: 1
                restriction = Restriction(
                    property_type=prop_template.name,
                    min_cardinality=1,
                    max_cardinality=None if prop_template.is_list else 1
                )
            else:
                # Optional fields get minCardinality: 0
                # Lists get maxCardinality: None (unbounded), single values get maxCardinality: 1
                restriction = Restriction(
                    property_type=prop_template.name,
                    min_cardinality=0,
                    max_cardinality=None if prop_template.is_list else 1
                )
            restrictions.append(restriction)
        
        # Create Type
        ro_crate_type = Type(
            id=type_template.id,  # Use id instead of name
            subclass_of=["https://schema.org/Thing"],
            ontological_annotations=[type_template.ontology] if type_template.ontology else [],
            rdfs_property=properties,
            comment=type_template.comment,
            label=type_template.id,  # Use id instead of name
            restrictions=restrictions
        )
        
        return ro_crate_type
    
    # Java API compatibility getter methods
    def get_types(self) -> List[Type]:
        """Get all types in the schema"""
        return self.types
    
    def getTypes(self) -> List[Type]:
        """Java API compatibility method to get all types"""
        return self.get_types()
    
    def get_type(self, type_id: str) -> Optional[Type]:
        """Get a specific type by its ID"""
        for type_obj in self.types:
            if type_obj.id == type_id:
                return type_obj
        return None

    def getType(self, type_id: str) -> Optional[Type]:
        """Java API compatibility method to get a specific type by its ID"""
        return self.get_type(type_id)

    def get_entries(self) -> List[MetadataEntry]:
        """Get all metadata entries in the schema"""
        return self.metadata_entries
    
    
    def get_entry(self, entry_id: str) -> Optional[MetadataEntry]:
        """Get a specific metadata entry by its ID"""
        for entry in self.metadata_entries:
            if entry.id == entry_id:
                return entry
        return None
    

    def get_entries_by_class(self, class_id: str) -> List[MetadataEntry]:
        """Get all metadata entries of a specific class"""
        return [entry for entry in self.metadata_entries if entry.class_id == class_id]
    
    def getEntries(self, class_id: str = "") -> List[MetadataEntry]:
        """Java API compatibility method to get all metadata entries of a specific class"""
        if not class_id:
            return self.get_entries()

        return self.get_entries_by_class(class_id)

    def get_entry_as(self, entry_id: str, target_type: TypingType) -> Optional[Any]:
        """
        Convert a metadata entry to an instance of the specified type.
        
        This method finds the metadata entry by ID and converts it to an instance
        of the provided target type (Pydantic model class or any other callable).
        
        Args:
            entry_id: The ID of the metadata entry to convert
            target_type: The target class/type to convert to (e.g., a Pydantic model)
            
        Returns:
            An instance of target_type created from the metadata entry, or None if entry not found
            
        Raises:
            ValueError: If the entry cannot be converted to the target type
            TypeError: If the target_type is not callable
            
        Example:
            facade = SchemaFacade.from_ro_crate("my_crate")
            
            # Define or get your Pydantic model
            class Person(BaseModel):
                name: str
                age: Optional[int] = None
                email: Optional[str] = None
            
            # Convert metadata entry to Pydantic instance
            person = facade.get_entry_as("person_001", Person)
            print(f"Name: {person.name}, Age: {person.age}")
            
            # Or use exported model from schema
            PersonModel = facade.export_pydantic_model("Person")
            person = facade.get_entry_as("person_001", PersonModel)
        """
        # Find the metadata entry
        entry = self.get_entry(entry_id)
        if not entry:
            return None
            
        # Check if target_type is callable
        if not callable(target_type):
            raise TypeError(f"target_type must be callable, got {type(target_type)}")
        
        try:
            # Use the ForwardRefResolver to handle recursive reference resolution
            constructor_data = self._forward_ref_resolver.resolve_metadata_references(
                self, entry_id, target_type
            )
            
            # Filter out any keys that aren't valid for the target type
            if hasattr(target_type, '__annotations__'):
                # For Pydantic models and annotated classes, only use valid fields
                valid_fields = set(getattr(target_type, '__annotations__', {}).keys())
                if hasattr(target_type, 'model_fields'):
                    # Pydantic v2 model fields
                    valid_fields.update(target_type.model_fields.keys())
                elif hasattr(target_type, '__fields__'):
                    # Pydantic v1 model fields
                    valid_fields.update(target_type.__fields__.keys())
                
                # Only pass valid fields to avoid unexpected keyword arguments
                if valid_fields:
                    constructor_data = {k: v for k, v in constructor_data.items() if k in valid_fields}
            
            # Create instance of target type
            instance = target_type(**constructor_data)
            return instance
            
        except Exception as e:
            raise ValueError(f"Failed to convert entry '{entry_id}' to {target_type.__name__}: {e}") from e
    
    # Property management methods
    def add_property_type(self, property: TypeProperty) -> 'SchemaFacade':
        """Add a standalone property to the schema registry"""
        # Check if already exists to avoid duplicates
        if not any(p.id == property.id for p in self.property_types):
            self.property_types.append(property)
            self._forward_ref_resolver.register(property.id, property)
        return self
        
    def add_restriction(self, restriction: Restriction) -> 'SchemaFacade':
        """Add a standalone restriction to the schema registry"""
        # Check if already exists to avoid duplicates
        if not any(r.id == restriction.id for r in self.restrictions):
            self.restrictions.append(restriction)
            self._forward_ref_resolver.register(restriction.id, restriction)
        return self
    
    def get_property_types(self) -> List[TypeProperty]:
        """Get all properties from all types in the schema, including standalone properties"""
        properties = []
        seen_ids = set()
        
        # Add standalone properties first
        for prop in self.property_types:
            if prop.id not in seen_ids:
                properties.append(prop)
                seen_ids.add(prop.id)
        
        # Add properties from types
        for type_obj in self.types:
            if type_obj.rdfs_property:
                for prop in type_obj.rdfs_property:
                    if prop.id not in seen_ids:
                        properties.append(prop)
                        seen_ids.add(prop.id)
        return properties
    
    def get_restrictions(self) -> List[Restriction]:
        """Get all restrictions, including standalone restrictions and those attached to types"""
        restrictions = []
        seen_ids = set()
        
        # Add standalone restrictions first
        for restriction in self.restrictions:
            if restriction.id not in seen_ids:
                restrictions.append(restriction)
                seen_ids.add(restriction.id)
        
        # Add restrictions from types (both explicit and auto-generated from properties)
        for type_obj in self.types:
            type_restrictions = type_obj.get_restrictions()  # This includes auto-generated ones
            for restriction in type_restrictions:
                if restriction.id not in seen_ids:
                    restrictions.append(restriction)
                    seen_ids.add(restriction.id)
        return restrictions
    
    def getRestrictions(self) -> List[Restriction]:
        """Java API compatibility method to get all restrictions"""
        return self.get_restrictions()
    
    def get_property_type(self, property_id: str) -> Optional[TypeProperty]:
        """Get a specific property by ID from anywhere in the schema"""
        # Check standalone properties first
        for prop in self.property_types:
            if prop.id == property_id:
                return prop
        
        # Check properties attached to types
        for type_obj in self.types:
            if type_obj.rdfs_property:
                for prop in type_obj.rdfs_property:
                    if prop.id == property_id:
                        return prop
        return None

    def getPropertyType(self, property_id: str) -> Optional[TypeProperty]:
        """Java API compatibility method to get a specific property by ID"""
        return self.get_property_type(property_id)
    
    def get_restriction(self, restriction_id: str) -> Optional[Restriction]:
        """Get a specific restriction by ID from anywhere in the schema"""
        # Check standalone restrictions first
        for restriction in self.restrictions:
            if restriction.id == restriction_id:
                return restriction
        
        # Check restrictions attached to types (both explicit and auto-generated)
        for type_obj in self.types:
            type_restrictions = type_obj.get_restrictions()
            for restriction in type_restrictions:
                if restriction.id == restriction_id:
                    return restriction
        return None

    def getRestriction(self, restriction_id: str) -> Optional[Restriction]:
        """Java API compatibility method to get a specific restriction by ID"""
        return self.get_restriction(restriction_id)

    # RO-Crate access method
    def get_crate(self, name: Optional[str] = None, description: Optional[str] = None, 
                  license: Optional[str] = None, **kwargs):
        """
        Get the underlying RO-Crate object with full schema and file integration.
        
        This method creates a complete RO-Crate object containing the schema,
        metadata entries, and any files that were added via add_file().
        Includes dynamic JSON-LD context based on actual vocabulary usage.
        
        Args:
            name: Name for the RO-Crate (optional)
            description: Description for the RO-Crate (optional)  
            license: License identifier for the RO-Crate (optional)
            **kwargs: Additional metadata for the RO-Crate
            
        Returns:
            ROCrate object ready for writing or further manipulation
        """
        from rocrate.rocrate import ROCrate
        from lib_ro_crate_schema.crate.jsonld_utils import add_schema_to_crate
        from datetime import datetime
        
        # Resolve any forward references first
        self.resolve_forward_refs()
        
        # Resolve placeholder entries (for circular references)
        self.resolve_placeholders()
        
        # Create the RO-Crate
        crate = ROCrate()
        
        # Set crate metadata
        if name:
            crate.name = name
        if description:
            crate.description = description
        if license:
            crate.license = license
            
        # Add any additional metadata
        for key, value in kwargs.items():
            setattr(crate, key, value)
        
        # Add dynamic JSON-LD context before adding schema
        dynamic_context = self.get_dynamic_context()
        if isinstance(dynamic_context, list) and len(dynamic_context) > 1:
            # Add the additional context (skip base RO-Crate context which is already included)
            additional_context = dynamic_context[1]
            if additional_context:  # Only if there are actually additional mappings
                crate.metadata.extra_contexts.append(additional_context)
        
        # Add schema to crate
        crate = add_schema_to_crate(self, crate)
        
        # Add files to crate
        if self.files:
            print(f"    📁 Adding {len(self.files)} files to RO-Crate:")
            for file_info in self.files:
                file_path = file_info['path']
                if file_path.exists():
                    # Create file properties
                    file_properties = {
                        "@type": "File",
                        "name": file_info['name'],
                        "description": file_info['description'],
                        "encodingFormat": self._get_mime_type(file_path),
                        "dateCreated": datetime.now().isoformat()
                    }
                    
                    # Add any custom properties
                    file_properties.update(file_info.get('properties', {}))
                    
                    # Add file to crate
                    file_entity = crate.add_file(
                        source=str(file_path),
                        properties=file_properties
                    )
                    print(f"      📄 Added: {file_path.name} ({file_info['name']})")
                else:
                    print(f"      ⚠️  File not found: {file_path}")
        
        return crate
    
    def getCrate(self, name: Optional[str] = None, description: Optional[str] = None, 
                 license: Optional[str] = None, **kwargs):
        """
        Java API compatibility alias for get_crate().
        
        Get the underlying RO-Crate object with full schema and file integration.
        
        Args:
            name: Name for the RO-Crate (optional)
            description: Description for the RO-Crate (optional)  
            license: License identifier for the RO-Crate (optional)
            **kwargs: Additional metadata for the RO-Crate
            
        Returns:
            ROCrate object ready for writing or further manipulation
        """
        return self.get_crate(name=name, description=description, license=license, **kwargs)
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file based on extension"""
        mime_types = {
            '.csv': 'text/csv',
            '.json': 'application/json', 
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.css': 'text/css',
            '.zip': 'application/zip',
            '.tar.gz': 'application/gzip',
            '.gz': 'application/gzip'
        }
        return mime_types.get(file_path.suffix.lower(), 'application/octet-stream')
