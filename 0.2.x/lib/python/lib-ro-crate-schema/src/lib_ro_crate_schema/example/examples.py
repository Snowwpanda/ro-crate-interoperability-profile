from lib_ro_crate_schema.crate.type import Type
from lib_ro_crate_schema.crate.type_property import TypeProperty
from lib_ro_crate_schema.crate.literal_type import LiteralType
from lib_ro_crate_schema.crate.metadata_entry import MetadataEntry

rdfs_type = Type(
    id="Creator",
    type="Type",
    subclass_of=["https://schema.org/Thing"],
    ontological_annotations=["https://www.dublincore.org/specifications/dublin-core/dcmi-terms/terms/creator//"],
    rdfs_property=None,
    comment="",
    label="",
    restrictions=None
)

serialized = rdfs_type.to_ro()
print(serialized.model_dump_json(by_alias=True))

# # Define properties for Creator
# has_name = TypeProperty(
#     id="hasName",
#     range_includes_data_type=[LiteralType.STRING]
# )

# has_identifier = TypeProperty(
#     id="hasIdentifier",
#     range_includes_data_type=[LiteralType.STRING],
#     ontological_annotations=["https://www.dublincore.org/specifications/dublin-core/dcmi-terms/elements11/identifier/"]
# )

# # Define the Creator type with its properties
# creator_type = Type(
#     id="Creator",
#     type="Type",
#     subclass_of=["https://schema.org/Thing"],
#     ontological_annotations=["https://www.dublincore.org/specifications/dublin-core/dcmi-terms/terms/creator//"],
#     rdfs_property=[has_name, has_identifier],
#     comment="",
#     label="",
#     restrictions=None
# )

# # Define properties for TextResource
# has_date_submitted = TypeProperty(
#     id="hasDateSubmitted",
#     range_includes_data_type=[LiteralType.DATETIME],
#     ontological_annotations=["https://www.dublincore.org/specifications/dublin-core/dcmi-terms/terms/dateSubmitted/"]
# )

# has_creator = TypeProperty(
#     id="hasCreator",
#     range_includes=[creator_type.id]
# )

# # Define the TextResource type with its properties
# text_resource_type = Type(
#     id="TextResource",
#     type="Type",
#     subclass_of=["https://schema.org/Thing"],
#     ontological_annotations=["https://www.dublincore.org/specifications/dublin-core/dcmi-terms/dcmitype/Text/"],
#     rdfs_property=[has_date_submitted, has_creator],
#     comment="",
#     label="",
#     restrictions=None
# )

# # Create metadata entries
# creator_entry = MetadataEntry(
#     id="creator1",
#     types={creator_type.id},
#     props={"hasName": "John Author", "hasIdentifier": "https://orcid.org/0000-0000-0000-0000"},
#     references={}
# )

# text_resource_entry = MetadataEntry(
#     id="TextResource1",
#     types={text_resource_type.id},
#     props={"hasDate": "2025-01-21T07:12:20Z"},
#     references={"hasCreator": ["creator1"]}
# )

# print(creator_entry.model_dump_json())