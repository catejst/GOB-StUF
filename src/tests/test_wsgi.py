import unittest
from unittest import mock

class TestWsgi(unittest.TestCase):

    @mock.patch('gobstuf.app.get_app')
    def test_wsgi(self, mock_get_app):
        import gobstuf.wsgi
        mock_get_app.assert_called()
