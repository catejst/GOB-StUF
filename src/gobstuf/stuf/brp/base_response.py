from abc import ABC, abstractmethod
from xml.etree.ElementTree import Element

from gobstuf.stuf.message import StufMessage
from gobstuf.stuf.exception import NoStufAnswerException
from gobstuf.stuf.brp.response_mapping import StufObjectMapping, Mapping


class StufResponse(ABC):
    """Base class. Wraps a StUF response.
    """

    # Predefined namespaces
    namespaces = {
        'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
        'BG': 'http://www.egem.nl/StUF/sector/bg/0310',
        'StUF': 'http://www.egem.nl/StUF/StUF0301',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }

    def __init__(self, msg: str, **kwargs):
        """

        :param msg: The string representation of the XML StUF message
        """
        self.stuf_message = None

        # Set kwargs as properties. For example inclusiefoverledenpersonen on the IngeschrevenpersonenStufResponse
        # class
        for k, v in kwargs.items():
            self.__setattr__(k, v)

        self.load(msg)

    def load(self, msg: str):
        self.stuf_message = StufMessage(msg, self.namespaces)

    def to_string(self):
        return self.stuf_message.pretty_print()


class MappedObjectWrapper:

    def __init__(self, mapped_object: dict, mapping_class: Mapping):
        self.mapped_object = mapped_object
        self.mapping_class = mapping_class

    def get_filtered_object(self, **kwargs):
        return self.mapping_class.filter(self.mapped_object, **kwargs)


class StufMappedResponse(StufResponse):
    """StufResponse with mapping for further use; maps paths to keys (as used in
    the REST API for example)

    """

    # Class properties to pass to the mapped object filter
    filter_kwargs = []

    def get_object_elm(self):
        """Returns the object wrapper element from the response message.

        :return:
        """
        answer_object = self.stuf_message.find_elm(self.answer_section)

        if not answer_object:
            raise NoStufAnswerException()

        return self.stuf_message.find_elm(self.object_elm, answer_object)

    def get_all_object_elms(self):
        """Returns all objects from the response message.

        Works like get_object_elm, but does not raise an Exception when there are no results.

        :return:
        """
        return self.stuf_message.find_all_elms(self.answer_section + ' ' + self.object_elm)

    def get_links(self, data):
        """
        Return the HAL links that correspond with the (self) mapped object

        Default implementation is to return no links

        :param data: the mapped and filtered object
        :return:
        """
        return {}

    def _get_filter_kwargs(self):
        return {prop: getattr(self, prop, None) for prop in self.filter_kwargs}

    def get_answer_object(self):
        """
        The answer object is created from the StUF response

        The response is mapped on the response object
        and then filtered

        If multiple answer objects are present, only the first item is returned.

        :return: the object to be returned as answer to the REST call
        :raises: NoStufAnswerException if the object is empty
        """
        mapped_object = self.get_mapped_object()
        answer_object = mapped_object.get_filtered_object(**self._get_filter_kwargs())

        if not answer_object:
            raise NoStufAnswerException()

        return answer_object

    def get_all_answer_objects(self):
        """
        Returns all objects from the StUF response. Works like get_answer_object, but does not raise an Exception when
        the response is empty.

        :return:
        """
        result = []
        for obj in self.get_all_object_elms():
            mapped_object = self.get_mapped_object(obj)
            answer_obj = mapped_object.get_filtered_object(**self._get_filter_kwargs())
            result.append(answer_obj)
        return result

    def _get_mapping(self, element: Element) -> Mapping:
        """Finds the mapping for the given XML Element, based on the value of StUF:entiteittype

        :param element:
        :return:
        """
        stuf_entity_type = element.attrib.get('{%s}entiteittype' % self.namespaces['StUF'])
        return StufObjectMapping.get_for_entity_type(stuf_entity_type)

    def get_mapped_object(self, obj=None, mapping=None):  # noqa: C901
        """
        Returns a dict with key -> value pairs for the keys in mapping with the value extracted
        from the response message.

        The mapping is a (possibly nested) dictionary. If no mapping is provided, the mapping will be inferred from
        the StUF:entiteittype attribute on the object.

        Each key is mapped upon the specified element value

        Optionally a tuple can be specified (method, element value).
        The element value is the passed as an argument to the given method

        Nested mappings are resolved by recursive calls to this method

        :return:
        """
        # Initially obj and mapping are None
        # On a recursive call these two parameters will have a value
        obj = obj or self.get_object_elm()
        mapping = mapping or self._get_mapping(obj)

        if isinstance(mapping, Mapping):
            # Initial call. Return mapped dictionary and Mapping class
            dict_mapping = self.get_mapped_object(obj, mapping.mapping)
            return MappedObjectWrapper(dict_mapping, mapping)
        elif isinstance(mapping, dict):
            # the values are resolved at a nested level by recursively calling this method
            # Example: 'naam': {'voornamen': '<attribute>', 'geslachtsnaam': '<attribute>'}
            return {k: self.get_mapped_object(obj, v) for k, v in mapping.items()}
        elif isinstance(mapping, tuple):
            # The value is resolved by a function call with the attribute value(s) as parameter(s)
            # Example: 'naamlengte': (len, '<attribute>')
            # will result in 'naamlengte': len(<attribute value>)
            method, *mappings = mapping
            attributes = [self.get_mapped_object(obj, v) for v in mappings]
            return method(*attributes)
        elif mapping and mapping[0] == '=':
            # Literal value, eg: =value results in value
            return mapping[1:]
        elif mapping and '!' in mapping:
            # XPath value, eg !.//<element>...
            mapping, path = mapping.split('!')
            return self.stuf_message.get_elm_value_by_path(mapping, path, obj)
        elif mapping and '@' in mapping:
            # Element attribute value, eg: element@attribute
            mapping, attr = mapping.split('@')
            return self.stuf_message.get_elm_attr(mapping, attr, obj)
        else:
            # Plain element value
            return self.stuf_message.get_elm_value(mapping, obj)

    @property
    @abstractmethod
    def answer_section(self):
        """The root element of the answer in the StUF message.

        :return:
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def object_elm(self):
        """The root element of the answer object, relative to the answer_secion

        :return:
        """
        pass  # pragma: no cover
