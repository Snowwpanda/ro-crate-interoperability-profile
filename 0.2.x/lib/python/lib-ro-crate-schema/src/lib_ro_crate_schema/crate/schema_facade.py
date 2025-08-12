# Constants from Java SchemaFacade
from typing import Literal



RDFS_CLASS: Literal["rdfs:Class"] = "rdfs:Class"
RDFS_PROPERTY: Literal["rdfs:Property"] = "rdfs:Property"
EQUIVALENT_CLASS: Literal["owl:equivalentClass"] = "owl:equivalentClass"
EQUIVALENT_CONCEPT: Literal["owl:equivalentProperty"] = "owl:equivalentProperty"
TYPE_RESTRICTION: Literal["owl:restriction"] = "owl:restriction"
RANGE_IDENTIFIER: Literal["schema:rangeIncludes"] = "schema:rangeIncludes"
DOMAIN_IDENTIFIER: Literal["schema:domainIncludes"] = "schema:domainIncludes"
OWL_MIN_CARDINALITY: Literal["owl:minCardinality"] = "owl:minCardinality"
OWL_MAX_CARDINALITY: Literal["owl:maxCardinality"] = "owl:maxCardinality"
OWL_RESTRICTION: Literal["owl:restriction"] = "owl:restriction"
ON_PROPERTY: Literal["owl:onProperty"] = "owl:onProperty"
RDFS_LABEL: Literal["rdfs:label"] = "rdfs:label"
RDFS_COMMENT: Literal["rdfs:comment"] = "rdfs:comment"
RDFS_SUBCLASS_OF: Literal["rdfs:subClassOf"] = "rdfs:subClassOf"

# Cardinality and other integer literals
MIN_CARDINALITY_MANDATORY: Literal[1] = 1
MAX_CARDINALITY_SINGLE: Literal[1] = 1
MAX_CARDINALITY_UNLIMITED: Literal[0] = 0

class SchemaFacade:
	def __init__(self):
		self.types = {}
		self.property_types = {}
		self.metadata_entries = {}

	def add_type(self, type_obj):
		self.types[type_obj.id] = type_obj

	def add_property_type(self, property_obj):
		self.property_types[property_obj.id] = property_obj

	def add_metadata_entry(self, entry_obj):
		self.metadata_entries[entry_obj.id] = entry_obj

	def serialize_ro_crate_graph(self):
		"""
		Serialize all types, property types, and metadata entries as RO-Crate @graph list.
		"""
		graph = []
		# Serialize types
		for t in self.types.values():
			graph.append(t.model_dump())
		# Serialize property types
		for p in self.property_types.values():
			graph.append(p.model_dump())
		# Serialize metadata entries
		for m in self.metadata_entries.values():
			graph.append(m.model_dump())
		return graph
