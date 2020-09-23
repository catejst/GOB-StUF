import logging

from gobstuf.config import GELF_HOST, GELF_PORT
from pygelf import GelfUdpHandler


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

        if GELF_HOST and GELF_PORT:
            # Only add Gelf handler when configured
            cls.instance.addHandler(GelfUdpHandler(host=GELF_HOST, port=int(GELF_PORT), include_extra_fields=True))


def get_default_logger():
    return Logger.get_instance()
