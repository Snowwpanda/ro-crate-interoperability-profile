package ch.eth.sis.rocrate.facade;

import java.io.Serializable;
import java.util.List;
import java.util.Map;
import java.util.Set;

public interface IMetadataEntry
{

    /**
     * Returns the ID of this entry
     */
    String getId();

    /* Returns the type ID of this entry */
    String getClassId();

    /* Returns the types of the entry */
    Set<String> getTypes();

    /* These are key-value pairs for serialization. These are single-valued.
     * Serializable classes are: String, Number and Boolean */
    Map<String, Serializable> getValues();

    /* These are references to other objects in the graph.
     * Each key may have one or more references */
    Map<String, List<String>> getReferences();

}
