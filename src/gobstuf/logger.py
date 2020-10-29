import logging

from flask import request, has_request_context

from gobstuf.config import CORRELATION_ID_HEADER, UNIQUE_ID_HEADER


class LogContextFilter(logging.Filter):

    def filter(self, record):
        """If in request context, add correlationID and uniqueID to log record.

        :param record:
        :return:
        """
        if has_request_context():
            # Keep spaces around correlationID and uniqueID values to make sure it's searchable in the logs.
            postfix = f"(correlationID: {request.headers.get(CORRELATION_ID_HEADER, '')} / " \
                      f"uniqueID: {request.headers.get(UNIQUE_ID_HEADER, '')} )"
            record.msg = f"{record.msg} {postfix}"
        return True


class Logger:
    """Singleton class

    """

    instance = None

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.init_logger()
        return cls.instance

    @classmethod
    def init_logger(cls):
        logging.basicConfig(level=logging.INFO)
        cls.instance = logging.getLogger()
        cls.instance.addFilter(LogContextFilter())


def get_default_logger():
    return Logger.get_instance()
