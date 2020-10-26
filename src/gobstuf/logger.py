import logging

from flask import request, has_request_context

from gobstuf.config import GELF_HOST, GELF_PORT, CORRELATION_ID_HEADER, UNIQUE_ID_HEADER
from pygelf import GelfUdpHandler


class LogContextFilter(logging.Filter):

    def filter(self, record):
        """If in request context, add correlationID and uniqueID to log record.

        :param record:
        :return:
        """
        if has_request_context():
            record.correlationID = request.headers.get(CORRELATION_ID_HEADER)
            record.uniqueID = request.headers.get(UNIQUE_ID_HEADER)
        return True


class Logger:
    """Singleton class

    """
    GELF_LOGGER = 'gelf'

    instance = None

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.init_logger()
        return cls.instance

    @classmethod
    def init_logger(cls):
        logging.basicConfig(level=logging.INFO)
        cls.instance = logging.getLogger(cls.GELF_LOGGER)
        cls.instance.addFilter(LogContextFilter())

        if GELF_HOST and GELF_PORT:
            # Initialise Gelf logger to be able to include extra fields
            cls.instance.addHandler(GelfUdpHandler(host=GELF_HOST, port=int(GELF_PORT), include_extra_fields=True))


def get_default_logger():
    return Logger.get_instance()
