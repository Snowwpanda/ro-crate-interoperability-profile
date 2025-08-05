package ch.eth.sis.rocrate.facade;

import java.util.ArrayList;
import java.util.List;

public class TypeProperty implements IPropertyType
{
    List<String> domainIncludes;

    List<String> rangeIncludes;

    String id;

    List<String> ontologicalAnnotations = new ArrayList<>();

    public List<String> getDomainIncludes()
    {
        return domainIncludes;
    }

    public void setDomainIncludes(List<String> domainIncludes)
    {
        this.domainIncludes = domainIncludes;
    }

    public void setRangeIncludes(List<String> rangeIncludes)
    {
        this.rangeIncludes = rangeIncludes;
    }

    public String getId()
    {
        return id;
    }

    @Override
    public List<String> getDomain()
    {
        return getDomainIncludes();
    }

    @Override
    public List<String> getRange()
    {
        return rangeIncludes;
    }

    @Override
    public List<String> getOntologicalAnnotations()
    {
        return ontologicalAnnotations;
    }

    public void setId(String id)
    {
        this.id = id;
    }

    public void setOntologicalAnnotations(List<String> ontologicalAnnotations)
    {
        this.ontologicalAnnotations = ontologicalAnnotations;
    }

    public void setTypes(List<IDataType> types)
    {
        this.rangeIncludes = new ArrayList<>(types.stream().map(IDataType::getTypeName).toList());
    }

    public void addType(IDataType type)
    {
        if (this.rangeIncludes == null)
        {
            this.rangeIncludes = new ArrayList<>();
        }
        if (!this.rangeIncludes.contains(type.getTypeName()))
        {
            this.rangeIncludes.add(type.getTypeName());
        }

    }
}
