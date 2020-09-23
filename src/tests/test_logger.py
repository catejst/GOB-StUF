from unittest import TestCase
from unittest.mock import patch

from gobstuf.logger import Logger, get_default_logger


class TestLogger(TestCase):

    @patch("gobstuf.logger.GelfUdpHandler")
    @patch("gobstuf.logger.logging")
    def test_get_instance(self, mock_logging, mock_gelf_handler):
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
