import freezegun

from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.app import handle_brp_regression_test_msg, SERVICEDEFINITION, run_message_thread, run, get_app


class TestApp(TestCase):

    @patch("gobstuf.app.ObjectstoreResultsWriter")
    @patch("gobstuf.app.BrpRegression")
    @patch("gobstuf.app.logger")
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
            'summary': mock_logger.get_summary()
        }, res)

    @patch("gobstuf.app.messagedriven_service")
    def test_run_message_thread(self, mock_messagedriven_service):
        run_message_thread()
        mock_messagedriven_service.assert_called_with(SERVICEDEFINITION, "StUF")

    @patch("gobstuf.app.Thread")
    @patch("gobstuf.app.get_flask_app")
    def test_get_app(self, mock_flask_app, mock_thread):
        self.assertEqual(mock_flask_app(), get_app())

        mock_thread.assert_called_with(target=run_message_thread)
        mock_thread().start.assert_called_once()

    @patch("gobstuf.app.GOB_STUF_PORT", 1234)
    @patch("gobstuf.app.get_app")
    def test_run(self, mock_get_app):
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        run()
        mock_app.run.assert_called_with(port=1234)
