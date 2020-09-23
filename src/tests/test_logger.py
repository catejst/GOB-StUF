from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.logger import Logger, get_default_logger, CORRELATION_ID_HEADER, UNIQUE_ID_HEADER, LogContextFilter


class TestLogContextFilter(TestCase):

    @patch("gobstuf.logger.has_request_context")
    @patch("gobstuf.logger.request")
    def test_filter(self, mock_request, mock_has_request_context):
        mock_request.headers = {
            CORRELATION_ID_HEADER: 'the correlation id',
            UNIQUE_ID_HEADER: 'the unique id',
        }
        mock_has_request_context.return_value = True

        mock_record = MagicMock()

        # Inside request context
        context_filter = LogContextFilter()
        context_filter.filter(mock_record)
        self.assertEqual('the correlation id', mock_record.correlationID)
        self.assertEqual('the unique id', mock_record.uniqueID)

        # Outside request context
        mock_has_request_context.return_value = False
        mock_record = MagicMock()
        mock_record.correlationID = None
        mock_record.uniqueID = None
        context_filter.filter(mock_record)
        self.assertIsNone(mock_record.correlationID)
        self.assertIsNone(mock_record.uniqueID)


class TestLogger(TestCase):

    @patch("gobstuf.logger.LogContextFilter")
    @patch("gobstuf.logger.GelfUdpHandler")
    @patch("gobstuf.logger.logging")
    def test_get_instance(self, mock_logging, mock_gelf_handler, mock_context_filter):
        """Testing get_instance and init_logger in same method, because mocking init_logger causes problems in this
        singleton class.

        :return:
        """

        # Test first instance
        Logger.instance = None
        res = Logger.get_instance()
        self.assertEqual(mock_logging.getLogger(), Logger.instance)
        self.assertEqual(Logger.instance, res)

        # Port 99 is set in __init__.py in the tests root directory
        mock_gelf_handler.assert_called_with(host='GELF_HOST', port=99, include_extra_fields=True)
        Logger.instance.addHandler.assert_called_with(mock_gelf_handler())
        Logger.instance.addFilter.assert_called_with(mock_context_filter())

        # Should not initialise logger again
        mock_logging.getLogger.reset_mock()
        res = Logger.get_instance()
        mock_logging.getLogger.assert_not_called()
        self.assertEqual(mock_logging.getLogger(), Logger.instance)
        self.assertEqual(Logger.instance, res)

        # Should initialise logger, but without Gelf logger
        Logger.instance = None
        with patch("gobstuf.logger.GELF_PORT", None):
            res = Logger.get_instance()
        self.assertEqual(mock_logging.getLogger(), Logger.instance)
        self.assertEqual(Logger.instance, res)
        Logger.instance.addHandler.assert_not_called()

    @patch("gobstuf.logger.Logger")
    def test_get_default_logger(self, mock_logger):
        self.assertEqual(mock_logger.get_instance(), get_default_logger())
