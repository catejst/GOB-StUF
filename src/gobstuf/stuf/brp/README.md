# BRP StUF Request and Response objects

## The StufRequest class
The StufRequest class is designed so that it is easy to add a new type of StufRequest. At the time of writing there is
one example of a StufRequest type class, which is the IngeschrevenpersonenStufRequest. This class defines four
properties, that together define the whole request.

A StufRequest is based on an XML template file, that contains a valid StufRequest. This makes it easy to see the actual
message when working on it. The XML template is defined in the ```template``` property.

When a StufRequest is initialised it requires an applicatie and gebruiker and a dict with values. The applicatie and
gebruiker are required for BRP requests to MKS and are inserted at the correct position in the XML message by the
StufRequest class. The values dict contains attributes with their values. For example, when
requesting a person, we need their BSN number. In this case the values dict contains the key 'bsn' with the BSN number as
value.
- The values in the values dict are inserted in the XML template at the paths as defined in the ```replace_paths```
property.
- The paths in the ```replace_paths``` property are relative to the path as defined in the ```content_root_elm``` property.

To request all possible MKS attributes use the following scope:
```xml
<BG:object StUF:entiteittype="NPS" StUF:scope="alles">
</BG:object>
```

When a StufRequest object is converted to its string representation (for actual sending), the values for 'tijdstip_bericht'
and 'referentienummer' are set automatically.
The StufRequest base object contains the generic paths for the applicatie, gebruiker, tijdstip_bericht and referentienummer
properties. These paths are also all relative to the ```content_root_elm``` property as set in the child object.

## The StufResponse class
The StufResponse class wraps a generic StufMessage and adds predefined namespaces used in the MKS StUF responses, so that
we can use these namespaces throughout the code without worrying that these namespaces change (or implementing other
workarounds). Being able to use consistent namespaces on our side makes the implementation a more comprehensible.
This class (and its childs) are initialised with the XML string.

### The StufMappedResponse class
A child of the StufResponse class that handles the mapping of the StUF response message to a dictionary of key -> values,
which is ultimately used to generated the REST response. A StufMappedResponse should implement three properties:
- ```mapping```, which maps logical names to XML paths. The paths are relative to the ```object_elm```
- ```object_elm```, the path to the object wrapper, relative to the ```answer_section```
- ```answer_section```, holding the path to the answer section in the StUF response. An empty answer section triggers
a ```NoStufAnswerException``` and is used in the API to trigger a 404.

### The StufErrorResponse class
Another child of the StufResponse class. Wraps an error response as returned by MKS. Exposes the fault code and string
from MKS.