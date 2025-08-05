package ch.eth.sis.rocrate.facade;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class MetadataEntry implements IMetadataEntry
{
    String id;

    String type;

    Map<String, Serializable> props;

    Map<String, List<String>> references;

    List<String> childrenIdentifiers = new ArrayList<>();

    List<String> parentIdentifiers = new ArrayList<>();

    public MetadataEntry()
    {
    }

    public MetadataEntry(String id, String type, Map<String, Serializable> props,
            Map<String, List<String>> references)
    {
        this.id = id;
        this.type = type;
        this.props = props;
        this.references = references;
    }

    public String getId()
    {
        return id;
    }

    @Override
    public String getClassId()
    {
        return type;
    }

    @Override
    public Map<String, Serializable> getValues()
    {
        return props;
    }

    @Override
    public Map<String, List<String>> getReferences()
    {
        return references;
    }

    public void setId(String id)
    {
        this.id = id;
    }

    @Override
    public String getType()
    {
        return type;
    }

    public void setType(String type)
    {
        this.type = type;
    }

    public void addChildIdentifier(String a)
    {
        childrenIdentifiers.add(a);
    }

    public void addParentIdentifier(String a)
    {
        parentIdentifiers.add(a);
    }

    public List<String> getChildrenIdentifiers()
    {
        return childrenIdentifiers;
    }

    public List<String> getParentIdentifiers()
    {
        return parentIdentifiers;
    }

    public void setProps(Map<String, Serializable> props)
    {
        this.props = props;
    }

    public void setReferences(Map<String, List<String>> references)
    {
        this.references = references;
    }
}
