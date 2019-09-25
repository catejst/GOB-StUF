import unittest
from unittest import mock

from gobstuf.api import _health, _routed_url, _update_response, _update_request
from gobstuf.api import _get_stuf, _post_stuf, _stuf
from gobstuf.api import get_app, run

class MockResponse:

    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


class TestAPI(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def test_health(self):
        result = _health()
        self.assertEqual(result, "Connectivity OK")

    def test_routed_url(self):
        result = _routed_url("proto://domain/path?args")
        self.assertEqual(result, "ROUTE_SCHEME://ROUTE_NETLOC/path?args")

        result = _routed_url("proto://domain/path?wsdl")
        self.assertEqual(result, "ROUTE_SCHEME://ROUTE_NETLOC/path?wsdl")

        result = _routed_url("proto://domain/path/?wsdl")
        self.assertEqual(result, "ROUTE_SCHEME://ROUTE_NETLOC/path?wsdl")

    def test_update_response(self):
        result = _update_response("text")
        self.assertEqual(result, "text")

        expect = "...localhost:GOB_STUF_PORT..."

        result = _update_response("...ROUTE_NETLOC...")
        self.assertEqual(result, expect)

        for n in [80, 800, 1234, 10000]:
            result = _update_response(f"...ROUTE_NETLOC:{n}...")
            self.assertEqual(result, expect)

        for n in [0, 123456]:
            result = _update_response(f"...ROUTE_NETLOC:{n}...")
            self.assertNotEqual(result, expect)

    def test_update_request(self):
        result = _update_request("...localhost:GOB_STUF_PORT...")
        self.assertEqual(result, "...ROUTE_NETLOC...")

        # Only convert full references
        result = _update_request("...localhost...")
        self.assertEqual(result, "...localhost...")


    @mock.patch("gobstuf.api.cert_get")
    def test_get_stuf(self, mock_get):
        mock_get.return_value = "get"

        response = _get_stuf("any url")
        self.assertEqual(response, "get")
        mock_get.assert_called_with("any url")

    @mock.patch("gobstuf.api.cert_post")
    def test_post_stuf(self, mock_post):
        mock_post.return_value = "post"

        url = "any url"
        data = "any data"
        headers = {
            "Soapaction": "Any action",
            "Content-Type": "text/xml",
            "Any other": "Any value"
        }
        expect_headers = {
            "Soapaction": "Any action",
            "Content-Type": "text/xml"
        }

        response = _post_stuf(url, data, headers)
        self.assertEqual(response, "post")
        mock_post.assert_called_with(url, data=data, headers=expect_headers)

        for h in [{},
                  {"Soapaction": "Any action"},
                  {"Soapaction": "Any action", "Content-Type": "any type"},
                  ]:
            with self.assertRaises(AssertionError):
                headers = h
                response = _post_stuf(url, data, headers)

    @mock.patch("gobstuf.api.AuditLogger")
    @mock.patch("gobstuf.api._get_stuf", return_value=MockResponse("get"))
    @mock.patch("gobstuf.api._post_stuf", return_value=MockResponse("post"))
    @mock.patch("gobstuf.api.flask")
    def test_stuf(self, mock_flask, mock_post, mock_get, mock_audit_logger):
        mock_flask.request.method = 'Any method'
        with self.assertRaises(AssertionError):
            _stuf()

        mock_flask.request.method = 'GET'
        mock_flask.request.url = "any url"

        response = _stuf()
        self.assertEqual(response.data, b"get")

        mock_flask.request.method = 'POST'
        mock_flask.request.data = b"any data"
        mock_flask.request.headers = {
            'Soapaction': 'zeepactie',
        }
        mock_flask.request.remote_addr = '1.2.3.4'

        mock_post.return_value = type('PostResponse', (object,), {'status_code': 123, 'text': 'response text'})

        response = _stuf()
        self.assertEqual(response.data, b"response text")

        # Make sure audit log is called
        audit_logger_instance = mock_audit_logger.get_instance.return_value
        audit_logger_instance.log_request.assert_called_with(
            '1.2.3.4',
            'ROUTE_SCHEME://ROUTE_NETLOC/any url',
            {
                'soapaction': 'zeepactie',
                'remote_response_code': 123,
                'original_url': 'any url',
                'method': 'POST',
            }
        )

    @mock.patch("gobstuf.api.CORS", mock.MagicMock())
    @mock.patch("gobstuf.api.Flask")
    def test_get_app(self, mock_flask):
        mock_app = mock.MagicMock()
        mock_flask.return_value = mock_app
        app = get_app()
        mock_flask.assert_called()
        mock_app.route.assert_called()

    @mock.patch("gobstuf.api.GOB_STUF_PORT", 1234)
    @mock.patch("gobstuf.api.get_app")
    def test_run(self, mock_get_app):
        mock_app = mock.MagicMock()
        mock_get_app.return_value = mock_app
        run()
        mock_app.run.assert_called_with(port=1234)

