import unittest
from unittest import mock

class TestMain(unittest.TestCase):

    @mock.patch('gobstuf.api.run')
    def test_main(self, mock_run):
        import gobstuf.__main__
        mock_run.assert_called()
