import unittest
import freezegun
from unittest.mock import MagicMock, call, patch

from gobstuf.__main__ import init, handle_brp_regression_test_msg, run_message_thread, SERVICEDEFINITION


class TestMain(unittest.TestCase):

    @patch("gobstuf.__main__.ObjectstoreResultsWriter")
    @patch("gobstuf.__main__.BrpRegression")
    @patch("gobstuf.__main__.logger")
    def test_handle_brp_regression_test_msg(self, mock_logger, mock_brp_regression, mock_writer):
        msg = {
            'header': {
                'header_attr': 'val',
            }
        }
        with freezegun.freeze_time('2020-08-03 15:30:00'):
            res = handle_brp_regression_test_msg(msg)

        mock_brp_regression.assert_called_with(mock_logger)
        mock_writer.assert_called_with(mock_brp_regression().run(), 'regression_tests/results/brp')
        mock_writer().write.assert_called_once()

        self.assertEqual({
            'header': {
                'header_attr': 'val',
                'timestamp': '2020-08-03T15:30:00',
            },
            'summary': {
                'warnings': mock_logger.get_warnings(),
                'errors': mock_logger.get_errors(),
            }
        }, res)

    @patch("gobstuf.__main__.messagedriven_service")
    def test_run_message_thread(self, mock_messagedriven_service):
        run_message_thread()
        mock_messagedriven_service.assert_called_with(SERVICEDEFINITION, "StUF")

    @patch("gobstuf.__main__.Thread")
    @patch("gobstuf.__main__.run_api")
    def test_init(self, mock_run, mock_thread):
        from gobstuf import __main__ as module
        m = MagicMock()
        m.attach_mock(mock_run, 'run')
        m.attach_mock(mock_thread, 'thread')

        with patch.object(module, '__name__', '__main__'):
            module.init()

        m.assert_has_calls([
            call.thread(target=run_message_thread),
            call.thread().start(),
            call.run(),
        ])
        mock_run.assert_called()
