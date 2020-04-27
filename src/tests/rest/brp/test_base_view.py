from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.rest.brp.base_view import (
    StufRestView, headers_required_decorator, MKS_USER_HEADER, MKS_APPLICATION_HEADER, HTTPError,
    NoStufAnswerException
)


class TestDecorator(TestCase):

    @patch("gobstuf.rest.brp.base_view.abort")
    @patch("gobstuf.rest.brp.base_view.request")
    @patch("gobstuf.rest.brp.base_view.Response")
    def test_headers_required_decorator(self, mock_response, mock_request, mock_abort):
        mock_request.headers = {'a': 'A', 'b': 'B'}
        decorated_f = MagicMock()

        # Success
        decorator = headers_required_decorator(['a', 'b'])
        inner_decorator = decorator(decorated_f)

        res = inner_decorator('arg1', 'arg2', kw1='kwarg1', kw2='kwarg2')
        self.assertEqual(decorated_f.return_value, res)
        decorated_f.assert_called_with('arg1', 'arg2', kw1='kwarg1', kw2='kwarg2')
        mock_abort.assert_not_called()

        decorated_f.reset_mock()

        # Abort, header 'c' is missing
        decorator = headers_required_decorator(['a', 'b', 'c'])
        inner_decorator = decorator(decorated_f)

        res = inner_decorator('arg1', 'arg2', kw1='kwarg1', kw2='kwarg2')

        # Return from abort is not necessary, but it keeps the code and tests clean
        self.assertEqual(mock_abort.return_value, res)
        decorated_f.assert_not_called()
        mock_abort.assert_called_with(mock_response.return_value)
        mock_response.assert_called_with(response='Missing required MKS headers', status=400)


class TestStufRestView(TestCase):

    @patch("gobstuf.rest.brp.base_view.abort")
    @patch("gobstuf.rest.brp.base_view.request")
    @patch("gobstuf.rest.brp.base_view.Response", MagicMock())
    def test_decorator_set(self, mock_request, mock_abort):
        # Tests if view is decorated with the correct required headers.

        # Next line should contain the minimal valid set of headers
        headers = {MKS_USER_HEADER: 'some value', MKS_APPLICATION_HEADER: 'some value'}

        set_decorator = StufRestView.decorators[0]

        # Check all headers present
        mock_request.headers = headers
        set_decorator(MagicMock())()
        mock_abort.assert_not_called()

        # Remove headers one by one and expect abort to be called
        for k in headers.keys():
            mock_abort.reset_mock()
            headers_copy = headers.copy()
            headers_copy.pop(k)
            mock_request.headers = headers_copy

            set_decorator(MagicMock())()
            mock_abort.assert_called_once()

    @patch("gobstuf.rest.brp.base_view.ROUTE_SCHEME", 'scheme')
    @patch("gobstuf.rest.brp.base_view.ROUTE_NETLOC", 'netloc')
    @patch("gobstuf.rest.brp.base_view.ROUTE_PATH", '/route/path')
    @patch("gobstuf.rest.brp.base_view.cert_post")
    def test_make_request(self, mock_post):
        stufreq = MagicMock()
        stufreq.soap_action = 'THE SOAP action'
        stufreq.to_string = lambda: 'string repr'

        view = StufRestView()
        self.assertEqual(mock_post.return_value, view._make_request(stufreq))

        mock_post.assert_called_with(
            'scheme://netloc/route/path',
            data='string repr',
            headers={
                'Soapaction': 'THE SOAP action',
                'Content-Type': 'text/xml',
            }
        )

    @patch("gobstuf.rest.brp.base_view.request")
    @patch("gobstuf.rest.brp.base_view.RESTResponse")
    def test_error_response(self, mock_rest_response, mock_request):
        mock_request.url = 'REQUEST_URL'
        view = StufRestView()
        response_arg = MagicMock()

        self.assertEqual(mock_rest_response.bad_request.return_value,
                         view._error_response(response_arg))

        # Generic error
        mock_rest_response.bad_request.assert_called_with()

        # Fo02 MKS error
        response_arg.get_error_code.return_value = 'Fo02'
        view._error_response(response_arg)

        mock_rest_response.forbidden.assert_called_with()

    @patch("gobstuf.rest.brp.base_view.request")
    @patch("gobstuf.rest.brp.base_view.StufErrorResponse")
    @patch("gobstuf.rest.brp.base_view.RESTResponse")
    def test_get(self, mock_rest_response, mock_response, mock_request):
        mock_request.headers = {
            MKS_USER_HEADER: 'user',
            MKS_APPLICATION_HEADER: 'application',
        }

        mock_request_template = MagicMock()
        mock_request_template.return_value.validate.return_value = None

        class StuffRestViewImpl(StufRestView):
            request_template = mock_request_template
            response_template = MagicMock()

        view = StuffRestViewImpl()
        view._make_request = MagicMock()
        view._error_response = MagicMock()
        view._json_response = MagicMock()

        # Success response
        self.assertEqual(mock_rest_response.ok.return_value, view._get(a=1, b=2))
        view.request_template.assert_called_with('user', 'application', {'a': 1, 'b': 2})
        view._make_request.assert_called_with(view.request_template.return_value)

        view.response_template.assert_called_with(view._make_request.return_value.text)
        mock_rest_response.ok.assert_called_with(view.response_template.return_value.get_answer_object.return_value,
                                                 view.response_template.return_value.get_links.return_value)

        # Error response
        view._make_request.return_value.raise_for_status.side_effect = HTTPError
        self.assertEqual(view._error_response.return_value, view._get(a=1, b=2))
        mock_response.assert_called_with(view._make_request.return_value.text)
        view._error_response.assert_called_with(mock_response.return_value)

        # 404 response
        view._make_request = MagicMock()
        view.response_template.return_value.get_answer_object.side_effect = NoStufAnswerException
        view._not_found_response = MagicMock()

        self.assertEqual(mock_rest_response.not_found(), view._get(a=1, b=2))

        # 400 Bad Request
        mock_request_template.return_value.validate.return_value = {'error': 'any error', 'code': 'any code'}
        view._bad_request_response = MagicMock()
        self.assertEqual(mock_rest_response.bad_request.return_value, view._get(a=1, b=2))
        mock_rest_response.bad_request.assert_called_with(error='any error', code='any code')

    @patch("gobstuf.rest.brp.base_view.RESTResponse")
    def test_get_internal_server_error(self, mock_rest_response):
        view = StufRestView()
        view._get = MagicMock()

        # Regular response
        result = view.get(any='thing')
        self.assertEqual(result, view._get.return_value)

        # Request failed for an unknown reason
        view._get.side_effect = Exception
        result = view.get(any='thing')
        self.assertEqual(result, mock_rest_response.internal_server_error.return_value)
