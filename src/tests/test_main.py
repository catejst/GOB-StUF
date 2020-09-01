import unittest
from unittest.mock import patch


class TestMain(unittest.TestCase):

    @patch("gobstuf.__main__.run_app")
    def test_init(self, mock_run):
        from gobstuf import __main__ as module

        with patch.object(module, '__name__', '__main__'):
            module.init()
        mock_run.assert_called()
