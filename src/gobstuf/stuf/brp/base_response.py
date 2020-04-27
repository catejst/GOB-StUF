from abc import ABC, abstractmethod

from gobstuf.stuf.message import StufMessage
from gobstuf.stuf.exception import NoStufAnswerException


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

    def __init__(self, msg: str):
        """

        :param msg: The string representation of the XML StUF message
        """
        self.stuf_message = None

        self.load(msg)

    def load(self, msg: str):
        self.stuf_message = StufMessage(msg, self.namespaces)

    def to_string(self):
        return self.stuf_message.pretty_print()


class StufMappedResponse(StufResponse):
    """StufResponse with mapping for further use; maps paths to keys (as used in
    the REST API for example)

    """
    def get_object_elm(self):
        """Returns the object wrapper element from the response message.

        :return:
        """
        answer_object = self.stuf_message.find_elm(self.answer_section)

        if not answer_object:
            raise NoStufAnswerException()

        return self.stuf_message.find_elm(self.object_elm, answer_object)

    def get_links(self):
        """
        Return the HAL links that correspond with the (self) mapped object

        Default implementation is to return no links

        :return:
        """
        return {}

    def get_answer_object(self):
        """
        The answer object is created from the StUF response

        The response is mapped on the response object
        and then filtered

        :return: the object to be returned as answer to the REST call
        :raises: NoStufAnswerException if the object is empty
        """
        mapped_object = self.get_mapped_object()
        answer_object = self.get_filtered_object(mapped_object)

        if not answer_object:
            raise NoStufAnswerException()

        return answer_object

    def get_filtered_object(self, mapped_object):
        """
        Filter the mapped object on the mapped attribute values
        Default implementation is to filter out any null values

        Any derived class that implements this method should call this super method on its result
        super().get_filtered_object(result)

        :param mapped_object:
        :return:
        """
        def filter_none_values(obj):
            """
            Recursively filter out any None values of the given object

            :param obj:
            :return:
            """
            result = {}
            for k, v in obj.items():
                if isinstance(v, dict):
                    value = filter_none_values(v)
                    if value:
                        result[k] = value
                elif v is not None:
                    result[k] = v
            return result

        return filter_none_values(mapped_object) if mapped_object else mapped_object

    def get_mapped_object(self, obj=None, mapping=None):
        """
        Returns a dict with key -> value pairs for the keys in mapping with the value extracted
        from the response message.

        The mapping is a (possibly nested) dictionary
        Each key is mapped upon the specified element value

        Optionally a tuple can be specified (method, element value).
        The element value is the passed as an argument to the given method

        Nested mappings are resolved by recursive calls to this method

        :return:
        """
        # Initially obj and mapping are None
        # On a recursive call these two parameters will have a value
        obj = obj or self.get_object_elm()
        mapping = mapping or self.mapping

        result = {}
        for k, v in mapping.items():
            if isinstance(v, dict):
                # the values are resolved at a nested level by recursively calling this method
                # Example: 'naam': {'voornamen': '<attribute>', 'geslachtsnaam': '<attribute>'}
                result[k] = self.get_mapped_object(obj, mapping[k])
            elif isinstance(v, tuple):
                # The value is resolved by a function call with the attribute value as a parameter
                # Example: 'naamlengte': (len, '<attribute>')
                # will result in 'naamlengte': len(<attribute value>)
                method, attribute = v
                result[k] = method(self.stuf_message.get_elm_value(attribute, obj))
            elif v[0] == '=':
                result[k] = v[1:]
            else:
                # Plain attribute value
                result[k] = self.stuf_message.get_elm_value(v, obj)
        return result

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

    @property
    @abstractmethod
    def mapping(self):
        """Mapping of keys to paths. Paths are relative to object_elm

        For example:
        {'burgerservicenummer': 'BG:inp.bsn'}

        :return:
        """
        pass  # pragma: no cover
