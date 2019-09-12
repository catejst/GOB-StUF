import unittest
from unittest import mock

from gobstuf.certrequest import cert_get, cert_post

class MockResponse:

    def __init__(self, status_code=0, reason=""):
        self.status_code = status_code
        self.reason = reason

class TestConfig(unittest.TestCase):

    def setUp(self) -> None:
        pass

    @mock.patch("gobstuf.certrequest.get")
    def test_get(self, mock_get):
        mock_get.return_value = MockResponse()

        response = cert_get("any url")
        mock_get.assert_called_with("any url", pkcs12_filename="PKCS12_FILENAME", pkcs12_password="PKCS12_PASSWORD")

        self.assertIsInstance(response, MockResponse)

    @mock.patch("gobstuf.certrequest.post")
    def test_post(self, mock_post):
        mock_post.return_value = MockResponse()

        cert_post("any url", "any data", {"a": 0})
        mock_post.assert_called_with("any url", data="any data", headers={"a": 0}, pkcs12_filename="PKCS12_FILENAME", pkcs12_password="PKCS12_PASSWORD")

        # headers is a default argument
        response = cert_post("any url", "any data")
        mock_post.assert_called_with("any url", data="any data", headers={}, pkcs12_filename="PKCS12_FILENAME", pkcs12_password="PKCS12_PASSWORD")

        self.assertIsInstance(response, MockResponse)
