package ch.eth.sis.rocrate.facade;

import java.io.Serializable;
import java.util.*;

public class MetadataEntry implements IMetadataEntry
{
    String id;

    Set<String> types;

    Map<String, Serializable> props;

    Map<String, List<String>> references;

    List<String> childrenIdentifiers = new ArrayList<>();

    List<String> parentIdentifiers = new ArrayList<>();

    public MetadataEntry()
    {
    }

    public MetadataEntry(String id, Set<String> types, Map<String, Serializable> props,
            Map<String, List<String>> references)
    {
        this.id = id;
        this.types = types;
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
        return null;
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
    public Set<String> getTypes()
    {
        return types;
    }

    public void setTypes(Set<String> types)
    {
        this.types = types;
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

    @Override
    public boolean equals(Object o)
    {
        if (this == o)
            return true;
        if (o == null || getClass() != o.getClass())
            return false;
        MetadataEntry entry = (MetadataEntry) o;
        return Objects.equals(id, entry.id) && Objects.equals(types, entry.types);
    }

    @Override
    public int hashCode()
    {
        return Objects.hash(id, types);
    }
}
