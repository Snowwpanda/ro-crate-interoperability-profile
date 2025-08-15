from typing import Literal

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
