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
        answer_object = self.stuf_message.find_elm(self.answer_section)

        if not answer_object:
            raise NoStufAnswerException()

        return self.stuf_message.find_elm(self.object_elm, answer_object)

    def get_mapped_object(self):
        obj = self.get_object_elm()
        return {k: self.stuf_message.get_elm_value(v, obj) for k, v in self.mapping.items()}

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
