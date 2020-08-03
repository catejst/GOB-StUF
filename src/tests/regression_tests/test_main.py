from unittest import TestCase
from unittest.mock import patch

from gobstuf.regression_tests.__main__ import main


class TestMain(TestCase):

    @patch("gobstuf.regression_tests.__main__.logging")
    @patch("gobstuf.regression_tests.__main__.BrpRegression")
    @patch("gobstuf.regression_tests.__main__.ObjectstoreResultsWriter")
    def test_main(self, mock_writer, mock_regression_test, mock_logging):
        main()

        mock_regression_test.assert_called_with(mock_logging.getLogger())
        mock_regression_test().run.assert_called_once()

        mock_writer.assert_called_with(mock_regression_test().run(), 'regression_tests/results/brp')
        mock_writer().write.assert_called_once()

    @patch("gobstuf.regression_tests.__main__.main")
    def test_module_main(self, mock_main):
        from gobstuf.regression_tests import __main__ as module
        with patch.object(module, '__name__', '__main__'):
            module.init()
            mock_main.assert_called_once()
