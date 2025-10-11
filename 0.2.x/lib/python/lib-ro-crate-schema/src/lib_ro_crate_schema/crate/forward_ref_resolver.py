from typing import TypeVar, Dict, Callable, Any, Union, Optional, List, Generic

from pydantic import BaseModel

T = TypeVar("T")
R = TypeVar("R")


class ForwardRef(BaseModel):
    """
    This internal class is used to mark
    properties as forward refs to be resolved
    """

    ref: str


class ForwardRefResolver(Generic[T]):
    """
    Instance-level resolver for managing forward references and dependency resolution within a SchemaFacade.
    
    This is NOT a global registry - each SchemaFacade gets its own ForwardRefResolver instance.
    It handles forward reference resolution, BFS dependency tracking, and Pydantic model caching
    for a specific schema context.
    
    Key features:
    - Store Type/Property objects by string keys for forward reference resolution
    - BFS dependency traversal for proper type ordering
    - Pydantic model caching to avoid regeneration
    - Handle circular dependencies through late binding
    """

    def __init__(self):
        self._store: Dict[str, T] = {}
        self._pydantic_models: Dict[str, type] = {}  # Cache for exported Pydantic models

    def register(self, key: str, value: T):
        self._store[key] = value

    def resolve(self, key: Union[ForwardRef, str]) -> T:
        """Resolve a ForwardRef or string key to the registered object"""
        if isinstance(key, ForwardRef):
            return self._store.get(key.ref)
        else:
            return self._store.get(key)

    def register_pydantic_model(self, type_id: str, model_class: type):
        """Register a generated Pydantic model for forward reference resolution"""
        self._pydantic_models[type_id] = model_class

    def get_pydantic_model(self, type_id: str) -> Optional[type]:
        """Get a previously registered Pydantic model"""
        return self._pydantic_models.get(type_id)

    def collect_dependencies_bfs(self, type_id: str) -> List[str]:
        """
        Collect all type dependencies using BFS traversal.
        Returns list of type IDs in dependency order (dependencies first).
        """
        from collections import deque
        
        visited = set()
        queue = deque([type_id])
        dependency_order = []
        
        while queue:
            current_type_id = queue.popleft()
            if current_type_id in visited:
                continue
                
            visited.add(current_type_id)
            current_type = self._store.get(current_type_id)
            
            if current_type and hasattr(current_type, 'rdfs_property'):
                # Find dependencies in this type's properties
                for prop in current_type.rdfs_property or []:
                    for range_type in prop.range_includes or []:
                        # Extract local name and check if it's a registered type
                        local_name = self._extract_local_id(range_type)
                        if local_name in self._store and local_name not in visited:
                            queue.append(local_name)
                            
            dependency_order.append(current_type_id)
            
        return dependency_order

    def get_all_dependencies(self, type_ids: Union[str, List[str]]) -> List[str]:
        """
        Get all dependencies for a type or multiple types, properly ordered.
        Returns deduplicated list with dependencies before dependents.
        
        Args:
            type_ids: Single type ID or list of type IDs to get dependencies for
            
        Returns:
            List of all unique type IDs in dependency order
        """
        # Handle single string input
        if isinstance(type_ids, str):
            type_ids = [type_ids]
            
        all_deps = []
        seen = set()
        
        for type_id in type_ids:
            deps = self.collect_dependencies_bfs(type_id)
            for dep in deps:
                if dep not in seen:
                    all_deps.append(dep)
                    seen.add(dep)
                    
        return all_deps

    @staticmethod
    def _extract_local_id(uri: str) -> str:
        """Extract local ID from URI (e.g., 'base:Person' → 'Person')"""
        if not uri:
            return ""
        if ":" in uri:
            return uri.split(":")[-1]
        return uri.split("/")[-1] if "/" in uri else uri

    def resolve_metadata_references(self, entry_resolver, entry_id: str, target_type: type, 
                                   processing_stack: set = None) -> dict:
        """
        Recursively resolve metadata entry references for proper Pydantic model construction.
        
        This method handles the conversion of metadata entry references to actual objects,
        preventing infinite loops and properly handling forward references.
        
        Args:
            entry_resolver: Object with get_entry(id) and get_entry_as(id, type) methods
            entry_id: ID of the metadata entry to resolve
            target_type: Target Pydantic model class
            processing_stack: Set of entry IDs currently being processed (for cycle detection)
            
        Returns:
            Dictionary with resolved references suitable for target_type constructor
        """
        if processing_stack is None:
            processing_stack = set()
            
        # Prevent infinite loops
        if entry_id in processing_stack:
            return {}
            
        processing_stack.add(entry_id)
        
        try:
            # Get the metadata entry
            entry = entry_resolver.get_entry(entry_id)
            if not entry:
                return {}
            
            # Start with direct properties
            resolved_data = {}
            resolved_data.update(entry.properties)
            
            # Handle references - resolve them to actual objects
            import typing
            from typing import Union, List
            
            annotations = getattr(target_type, '__annotations__', {})
            
            # First process actual references
            for ref_name, ref_ids in entry.references.items():
                if not ref_ids:  # Skip empty reference lists
                    continue
                    
                expected_type = annotations.get(ref_name)
                
                # Handle Optional[Type] by extracting Type
                if expected_type and hasattr(expected_type, '__origin__'):
                    if hasattr(typing, 'get_origin') and typing.get_origin(expected_type) is Union:
                        args = typing.get_args(expected_type)
                        if len(args) == 2 and type(None) in args:
                            expected_type = args[0] if args[1] is type(None) else args[1]
                
                # Check if it's a list type
                is_list_type = False
                list_element_type = str
                if expected_type and hasattr(expected_type, '__origin__'):
                    if hasattr(typing, 'get_origin') and typing.get_origin(expected_type) in (list, List):
                        is_list_type = True
                        args = typing.get_args(expected_type)
                        if args:
                            list_element_type = args[0]
                            expected_type = list_element_type
                
                resolved_refs = []
                
                for ref_id in ref_ids:
                    # Resolve forward references to actual types first
                    resolved_expected_type = expected_type
                    if hasattr(expected_type, '__forward_arg__'):
                        # This is a forward reference, try to resolve it
                        forward_name = expected_type.__forward_arg__
                        # Handle cases with extra quotes like "'Equipment'" -> "Equipment"
                        if forward_name.startswith("'") and forward_name.endswith("'"):
                            forward_name = forward_name[1:-1]
                        
                        # Try to resolve using the entry resolver (which should have the pydantic models)
                        if hasattr(entry_resolver, 'export_pydantic_model'):
                            try:
                                resolved_expected_type = entry_resolver.export_pydantic_model(forward_name)
                            except:
                                # Fallback: if forward name matches target type
                                if forward_name == target_type.__name__:
                                    resolved_expected_type = target_type
                        elif forward_name == target_type.__name__:
                            resolved_expected_type = target_type
                    
                    if resolved_expected_type and resolved_expected_type != str and callable(resolved_expected_type):
                        try:
                            # Recursively resolve referenced entries using this same method
                            if ref_id not in processing_stack:
                                resolved_ref_data = self.resolve_metadata_references(
                                    entry_resolver, ref_id, resolved_expected_type, processing_stack
                                )
                                
                                if resolved_ref_data:
                                    # Create instance of expected type
                                    resolved_ref = resolved_expected_type(**resolved_ref_data)
                                    resolved_refs.append(resolved_ref)
                                else:
                                    # Fallback to ID if resolution fails
                                    resolved_refs.append(ref_id)
                            else:
                                # Circular reference - use ID
                                resolved_refs.append(ref_id)
                        except Exception as e:
                            # Fallback to ID if conversion fails
                            resolved_refs.append(ref_id)
                    else:
                        # Expected type is string or not resolvable
                        resolved_refs.append(ref_id)
                
                # Set the resolved reference(s)
                if is_list_type:
                    resolved_data[ref_name] = resolved_refs
                elif len(resolved_refs) == 1:
                    resolved_data[ref_name] = resolved_refs[0]
                elif len(resolved_refs) > 1:
                    resolved_data[ref_name] = resolved_refs  # Multiple refs for single field
                else:
                    resolved_data[ref_name] = None
            
            # Handle properties that should be references but are stored as string representations
            # (This happens when objects were serialized incorrectly during export)
            for prop_name, prop_value in entry.properties.items():
                expected_type = annotations.get(prop_name)
                
                # Skip if we already processed this as a reference
                if prop_name in entry.references:
                    continue
                
                # Handle Optional[Type] by extracting Type
                if expected_type and hasattr(expected_type, '__origin__'):
                    if hasattr(typing, 'get_origin') and typing.get_origin(expected_type) is Union:
                        args = typing.get_args(expected_type)
                        if len(args) == 2 and type(None) in args:
                            expected_type = args[0] if args[1] is type(None) else args[1]
                
                # Resolve forward references to actual types
                actual_expected_type = expected_type
                if hasattr(expected_type, '__forward_arg__'):
                    # This is a forward reference, try to resolve it
                    forward_name = expected_type.__forward_arg__
                    # Handle cases with extra quotes like "'Equipment'" -> "Equipment"
                    if forward_name.startswith("'") and forward_name.endswith("'"):
                        forward_name = forward_name[1:-1]
                    
                    # Try to resolve using the entry resolver (which should have the pydantic models)
                    if hasattr(entry_resolver, 'export_pydantic_model'):
                        try:
                            actual_expected_type = entry_resolver.export_pydantic_model(forward_name)
                        except:
                            # Fallback: if forward name matches target type
                            if forward_name == target_type.__name__:
                                actual_expected_type = target_type
                    elif forward_name == target_type.__name__:
                        actual_expected_type = target_type
                
                # If expected type is a Pydantic model and we have a string representation
                if (actual_expected_type and 
                    hasattr(actual_expected_type, '__bases__') and 
                    any('BaseModel' in str(base) for base in actual_expected_type.__bases__) and
                    isinstance(prop_value, str) and
                    prop_value.startswith("{") and prop_value.endswith("}")):
                    
                    try:
                        # Try to parse the string as a Python dict representation, but handle datetime objects
                        # First, replace datetime.datetime(...) with a parseable format
                        import re
                        
                        # Replace datetime.datetime(year, month, day, ...) with ISO string
                        def datetime_replacer(match):
                            # Extract the datetime arguments
                            args_str = match.group(1)
                            try:
                                # Parse basic datetime(year, month, day, hour, minute) pattern
                                args = [int(x.strip()) for x in args_str.split(',')]
                                if len(args) >= 3:
                                    from datetime import datetime
                                    dt = datetime(*args[:6])  # year, month, day, hour, minute, second
                                    return f"'{dt.isoformat()}'"
                            except (ValueError, TypeError):
                                pass
                            return "'1900-01-01T00:00:00'"  # fallback
                        
                        cleaned_value = re.sub(r'datetime\.datetime\(([^)]+)\)', datetime_replacer, prop_value)
                        
                        import ast
                        parsed_dict = ast.literal_eval(cleaned_value)
                        
                        # Create an instance of the expected type from the parsed data
                        if isinstance(parsed_dict, dict):
                            # Recursively handle nested objects
                            nested_resolved = {}
                            nested_annotations = getattr(actual_expected_type, '__annotations__', {})
                            
                            for key, value in parsed_dict.items():
                                nested_expected_type = nested_annotations.get(key)
                                
                                # Handle nested Optional[Type]
                                if nested_expected_type and hasattr(nested_expected_type, '__origin__'):
                                    if hasattr(typing, 'get_origin') and typing.get_origin(nested_expected_type) is Union:
                                        nested_args = typing.get_args(nested_expected_type)
                                        if len(nested_args) == 2 and type(None) in nested_args:
                                            nested_expected_type = nested_args[0] if nested_args[1] is type(None) else nested_args[1]
                                
                                # Convert datetime strings back to datetime objects if needed
                                if key == 'created_date' and isinstance(value, str):
                                    from datetime import datetime
                                    try:
                                        value = datetime.fromisoformat(value)
                                    except (ValueError, TypeError):
                                        pass
                                
                                nested_resolved[key] = value
                            
                            resolved_instance = actual_expected_type(**nested_resolved)
                            resolved_data[prop_name] = resolved_instance
                    except (ValueError, SyntaxError, TypeError) as e:
                        # If parsing fails, keep the original string value
                        pass
            
            return resolved_data
            
        finally:
            processing_stack.discard(entry_id)

    def clear(self):
        self._store.clear()
        self._pydantic_models.clear()
