package ch.eth.sis.rocrate;

import ch.eth.sis.rocrate.facade.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import edu.kit.datamanager.ro_crate.RoCrate;
import edu.kit.datamanager.ro_crate.entities.data.DataEntity;

import java.io.Serializable;
import java.util.*;

public class SchemaFacade implements ISchemaFacade
{

    private final static String RDFS_CLASS = "rdfs:Class";

    private final static String RDFS_PROPERTY = "rdfs:Property";

    public static final String EQUIVALENT_CLASS = "owl:equivalentClass";

    public static final String EQUIVALENT_CONCEPT = "owl:equivalentProperty";


    private Map<String, IType> types;

    private Map<String, IPropertyType> propertyTypes;

    private Map<String, IMetadataEntry> metadataEntries;

    private final RoCrate crate;

    public SchemaFacade(RoCrate crate)
    {
        this.crate = crate;
        this.types = new LinkedHashMap<>();
        this.propertyTypes = new LinkedHashMap<>();
        this.metadataEntries = new LinkedHashMap<>();
    }

    public static SchemaFacade of(RoCrate crate) throws JsonProcessingException
    {
        SchemaFacade schemaFacade = new SchemaFacade(crate);
        schemaFacade.parseEntities();
        return schemaFacade;

    }

    @Override
    public void addType(IType rdfsClass)
    {

        DataEntity.DataEntityBuilder builder = new DataEntity.DataEntityBuilder();
        builder.addProperty("@id", rdfsClass.getId());
        builder.addProperty("@type", RDFS_CLASS);
        rdfsClass.getSubClassOf().forEach(x -> builder.addIdProperty("rdfs:subClassOf", x));
        this.types.put(rdfsClass.getId(), rdfsClass);
        DataEntity entity = builder.build();
        entity.addIdListProperties(EQUIVALENT_CLASS, rdfsClass.getOntologicalAnnotations());
        crate.addDataEntity(entity);

    }

    @Override
    public List<IType> getTypes()
    {
        return this.types.values().stream().toList();
    }

    @Override
    public IType getTypes(String id)
    {
        return this.types.get(id);
    }

    @Override
    public void addPropertyType(IPropertyType rdfsProperty)
    {
        DataEntity.DataEntityBuilder builder = new DataEntity.DataEntityBuilder();

        builder.setId(rdfsProperty.getId());
        builder.addProperty("@type", RDFS_PROPERTY);

        var stuff = builder.build();
        stuff.addIdListProperties("schema:rangeIncludes",
                rdfsProperty.getRange());
        stuff.addIdListProperties("schema:domainIncludes",
                rdfsProperty.getDomain());
        stuff.addIdListProperties(EQUIVALENT_CONCEPT,
                rdfsProperty.getOntologicalAnnotations());
        crate.addDataEntity(stuff);
        propertyTypes.put(rdfsProperty.getId(), rdfsProperty);

    }

    @Override
    public List<IPropertyType> getPropertyTypes()
    {
        return propertyTypes.values().stream().toList();
    }

    @Override
    public IPropertyType getPropertyType(String id)
    {
        return propertyTypes.get(id);
    }

    @Override
    public void addEntry(IMetadataEntry metaDataEntry)
    {
        DataEntity.DataEntityBuilder builder = new DataEntity.DataEntityBuilder();
        builder.setId(metaDataEntry.getId());
        builder.addProperty("@type", metaDataEntry.getClassId());
        ObjectMapper objectMapper = new ObjectMapper();

        metaDataEntry.getValues().forEach((s, o) -> {
            if (o instanceof Double)
            {
                builder.addProperty(s, (Double) o);
            } else if (o instanceof Integer)
            {
                builder.addProperty(s, (Integer) o);
            } else if (o instanceof Boolean)
            {
                builder.addProperty(s, (Boolean) o);
            } else if (o instanceof String)
            {
                builder.addProperty(s, o.toString());
            } else if (o == null)
            {
                builder.addProperty(s, objectMapper.nullNode());
            }
        });
        DataEntity dataEntity = builder.build();
        metaDataEntry.getReferences().forEach(dataEntity::addIdListProperties);

        crate.addDataEntity(dataEntity);

    }

    @Override
    public IMetadataEntry getEntry(String id)
    {
        return metadataEntries.get(id);
    }

    @Override
    public List<IMetadataEntry> getEntries(String rdfsClassId)
    {
        return metadataEntries.values().stream().toList();
    }

    private void parseEntities() throws JsonProcessingException
    {
        Map<String, IPropertyType> properties = new LinkedHashMap<>();
        Map<String, IType> classes = new LinkedHashMap<>();
        Map<String, IMetadataEntry> entries = new LinkedHashMap<>();

        for (DataEntity entity : crate.getAllDataEntities())
        {
            String type = entity
                    .getProperty("@type").asText();
            String id =
                    entity.getProperty("@id")
                            .asText();

            switch (type)
            {
                case "rdfs:Class" ->
                {
                    RdfsClass rdfsClass = new RdfsClass();
                    rdfsClass.setSubClassOf(parseMultiValued(entity, "rdfs:subClassOf"));
                    rdfsClass.setOntologicalAnnotations(
                            parseMultiValued(entity, EQUIVALENT_CLASS));
                    rdfsClass.setId(id);
                    classes.put(id, rdfsClass);

                }
                case "rdfs:Property" ->
                {
                    TypeProperty rdfsProperty = new TypeProperty();
                    rdfsProperty.setId(id);
                    rdfsProperty.setOntologicalAnnotations(
                            parseMultiValued(entity, EQUIVALENT_CONCEPT));
                    rdfsProperty.setRangeIncludes(
                            parseMultiValued(entity, "schema:rangeIncludes"));
                    rdfsProperty.setDomainIncludes(
                            parseMultiValued(entity, "schema:domainIncludes"));
                    properties.put(id, rdfsProperty);

                }

            }

        }

        for (var entity : crate.getAllDataEntities())
        {
            String type = entity
                    .getProperty("@type").asText();
            String id =
                    entity.getProperty("@id")
                            .asText();
            if (!classes.containsKey(type))
            {
                continue;
            }

            Map<String, Serializable> entryProperties = new LinkedHashMap<>();
            MetadataEntry entry = new MetadataEntry();
            entry.setId(id);
            entry.setType(type);
            ObjectMapper objectMapper = new ObjectMapper();
            Map<String, Serializable> keyVals =
                    objectMapper.readValue(entity.getProperties().toString(), HashMap.class);
            for (Map.Entry<String, Serializable> a : keyVals.entrySet())
            {
                if (properties.containsKey(a.getKey()))
                {
                    IPropertyType property = properties.get(a.getKey());
                    if (property.getRange().stream().anyMatch(x -> x.equals("xsd:string")))
                    {
                        entryProperties.put(a.getKey(), a.getValue().toString());
                    }
                }
            }
            entry.setProps(entryProperties);
            entry.setReferences(new HashMap<>());
            entries.put(id, entry);
        }
        System.out.println("Done");
        this.types = classes;
        this.propertyTypes = properties;
        this.metadataEntries = entries;

    }

    private List<String> parseMultiValued(DataEntity dataEntity, String key)
    {
        JsonNode node = dataEntity.getProperty(key);
        if (node instanceof ObjectNode)
        {
            return List.of(node.get("@id").textValue());
        }
        if (node instanceof ArrayNode arrayNode)
        {
            List<String> accumulator = new ArrayList<>();
            arrayNode.elements().forEachRemaining(
                    x -> accumulator.add(x.get("@id").textValue())
            );
            return accumulator;
        }
        return List.of();

    }
}
