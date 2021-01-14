from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.logger import Logger, get_default_logger, CORRELATION_ID_HEADER, UNIQUE_ID_HEADER, LogContextFilter


class TestLogContextFilter(TestCase):

    @patch("gobstuf.logger.has_request_context")
    def test_filter(self, mock_has_request_context):
        mock_request = MagicMock()

        with patch("gobstuf.logger.request", mock_request):
            mock_request.headers = {
                CORRELATION_ID_HEADER: 'the correlation id',
                UNIQUE_ID_HEADER: 'the unique id',
            }
            mock_has_request_context.return_value = True

            mock_record = MagicMock()
            mock_record.msg = 'The log message'

            # Inside request context
            context_filter = LogContextFilter()
            context_filter.filter(mock_record)
            self.assertEqual('The log message (correlationID: the correlation id / uniqueID: the unique id )', mock_record.msg)

            # Outside request context
            mock_has_request_context.return_value = False
            mock_record = MagicMock()
            mock_record.msg = 'The log message'
            context_filter.filter(mock_record)
            self.assertEqual('The log message', mock_record.msg)


class TestLogger(TestCase):

    @patch("gobstuf.logger.LogContextFilter")
    @patch("gobstuf.logger.logging")
    def test_get_instance(self, mock_logging, mock_context_filter):
        """Testing get_instance and init_logger in same method, because mocking init_logger causes problems in this
        singleton class.

        :return:
        """

        # Test first instance
        Logger.instance = None
        res = Logger.get_instance()
        self.assertEqual(mock_logging.getLogger(), Logger.instance)
        self.assertEqual(Logger.instance, res)

        Logger.instance.addFilter.assert_called_with(mock_context_filter())

        # Should not initialise logger again
        mock_logging.getLogger.reset_mock()
        res = Logger.get_instance()
        mock_logging.getLogger.assert_not_called()
        self.assertEqual(mock_logging.getLogger(), Logger.instance)
        self.assertEqual(Logger.instance, res)

    @patch("gobstuf.logger.Logger")
    def test_get_default_logger(self, mock_logger):
        self.assertEqual(mock_logger.get_instance(), get_default_logger())
