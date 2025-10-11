#!/usr/bin/env python3
"""
Python QuickStart Write Example
Mirrors the Java Quickstart.java for exact compatibility demonstration
"""

import sys
sys.path.append('src')

from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry
from lib_ro_crate_schema.crate.literal_type import LiteralType


# Constants (matching Java pattern exactly)
TMP_EXAMPLE_CRATE = "output_crates/example-crate"

def write_example_crate():
    """
    Python QuickStart matching Java Quickstart structure exactly
    Demonstrates compatibility between Java and Python RO-Crate implementations
    """
    
    PREFIX = "" #Example"
    SEPARATOR = "" #:"
    
    # Setting up an RO-Crate with the schema facade (matching Java constructor pattern)
    schemaFacade = SchemaFacade()
    
    personType = Type(id="id")  # Temporary ID for pydantic requirement
    
    # Block 1: Person type setup (matching Java structure exactly)
    personType.setId(PREFIX + SEPARATOR + "Person")
    personType.setOntologicalAnnotations(["https://schema.org/Person"])
    
    # Block 2: Person ID property (matching Java block structure)
    personId = TypeProperty(id="id")  # Temporary ID for pydantic requirement
    personId.setId(PREFIX + SEPARATOR + "personid")
    personId.setTypes([LiteralType.STRING])
    personType.addProperty(personId)
    
    # Block 3: Given name property (matching Java block structure)  
    givenName = TypeProperty(id="id")  # Temporary ID for pydantic requirement
    givenName.setId(PREFIX + SEPARATOR + "givenName")
    givenName.setOntologicalAnnotations(["https://schema.org/givenName"])
    givenName.setTypes([LiteralType.STRING])
    personType.addProperty(givenName)
    
    # Block 4: Family name property (matching Java block structure)
    familyName = TypeProperty(id="id")  # Temporary ID for pydantic requirement  
    familyName.setId(PREFIX + SEPARATOR + "familyName")
    familyName.setOntologicalAnnotations(["https://schema.org/familyName"])
    familyName.setTypes([LiteralType.STRING])
    personType.addProperty(familyName)
    
    # Block 5: Identifier property (matching Java block structure)
    identifier = TypeProperty(id="id")  # Temporary ID for pydantic requirement
    identifier.setId(PREFIX + SEPARATOR + "identifier")
    identifier.setOntologicalAnnotations(["https://schema.org/identifier"])
    identifier.setTypes([LiteralType.STRING])
    personType.addProperty(identifier)
    
    schemaFacade.addType(personType)
    
    # Building Experiment type (matching Java block structure)
    experimentType = Type(id="id")  # Temporary ID for pydantic requirement
    experimentType.setId(PREFIX + SEPARATOR + "Experiment")
    
    # Block 1: Experiment ID property (matching Java block structure)
    experimentId = TypeProperty(id="id")  # Temporary ID for pydantic requirement
    experimentId.setId(PREFIX + SEPARATOR + "experimentid")
    experimentId.setTypes([LiteralType.STRING])
    experimentType.addProperty(experimentId)
    
    # Block 2: Creator property (matching Java block structure)
    creator = TypeProperty(id="id")  # Temporary ID for pydantic requirement
    creator.setId(PREFIX + SEPARATOR + "creator")
    creator.setOntologicalAnnotations(["https://schema.org/creator"])
    creator.addType(personType)  # References the personType (matching Java pattern)
    experimentType.addProperty(creator)
    
    # Block 3: Name property (matching Java block structure)
    name = TypeProperty(id="id")  # Temporary ID for pydantic requirement
    name.setId(PREFIX + SEPARATOR + "name")
    name.setTypes([LiteralType.STRING])
    experimentType.addProperty(name)
    
    # Block 4: Date property (matching Java block structure)
    date = TypeProperty(id="id")  # Temporary ID for pydantic requirement
    date.setId(PREFIX + SEPARATOR + "date")
    date.setTypes([LiteralType.DATETIME])
    experimentType.addProperty(date)
    
    schemaFacade.addType(experimentType)
    
    # Creating metadata entries (matching Java block structure exactly)
    
    # Block 1: Person Andreas (matching Java structure)
    personAndreas = MetadataEntry(id="id", class_id="id")  # Temporary values for pydantic requirement
    personAndreas.setId("PERSON1")
    personAndreas.setClassId(personType.getId())
    properties = {}
    properties["givenname"] = "Andreas"
    properties["lastname"] = "Meier"
    properties["identifier"] = "https://orcid.org/0009-0002-6541-4637"
    personAndreas.setProperties(properties)
    personAndreas.setReferences({})
    schemaFacade.addEntry(personAndreas)
    
    # Block 2: Person Juan (matching Java structure) - Note: Java has "Andreas" twice, following that pattern
    personJuan = MetadataEntry(id="id", class_id="id")  # Temporary values for pydantic requirement
    personJuan.setId("PERSON2")
    personJuan.setClassId(personType.getId())
    properties2 = {}
    properties2["givenname"] = "Juan"  # Matching Java code (has Andreas for both persons)
    properties2["lastname"] = "Meier"
    properties2["identifier"] = "https://orcid.org/0009-0002-6541-4637"
    personJuan.setProperties(properties2)
    personJuan.setReferences({})
    schemaFacade.addEntry(personJuan)
    
    # Block 3: Experiment 1 (matching Java structure)
    experiment1 = MetadataEntry(id="id", class_id="id")  # Temporary values for pydantic requirement
    experiment1.setId("EXPERIMENT1")
    experiment1.setClassId(experimentType.getId())
    experiment1.setReferences({"creator": [personAndreas.getId()]})
    propertiesExperiment = {}
    propertiesExperiment["name"] = "Example Experiment"
    propertiesExperiment["date"] = "2025-09-08 08:41:50.000"  # ISO 8601
    experiment1.setProperties(propertiesExperiment)
    schemaFacade.addEntry(experiment1)
    
    # Write to file (matching Java FolderWriter pattern)
    schemaFacade.write(TMP_EXAMPLE_CRATE, name="Python QuickStart Example")


if __name__ == "__main__":
    write_example_crate()