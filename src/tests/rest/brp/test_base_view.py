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

    @patch("gobstuf.rest.brp.base_view.Document")
    @patch("gobstuf.rest.brp.base_view.Response")
    def test_json_response(self, mock_response, mock_document):
        data = {'some': 'dict'}

        view = StufRestView()
        self.assertEqual((mock_response.return_value, 200), view._json_response(data))
        mock_document.assert_called_with(data=data)
        mock_response.assert_called_with(
            response=mock_document.return_value.to_json.return_value,
            content_type='application/hal+json'
        )

        # Test with status code specified
        self.assertEqual((mock_response.return_value, 123), view._json_response(data, 123))

    def test_error_response(self):
        view = StufRestView()
        response_arg = MagicMock()
        view._json_response = MagicMock()

        self.assertEqual(view._json_response(), view._error_response(response_arg))

        # Generic error
        view._json_response.assert_called_with({
            'mks_code': response_arg.get_error_code(),
            'mks_error': response_arg.get_error_string(),
        }, 400)

        # Fo02 MKS error
        response_arg.get_error_code.return_value = 'Fo02'
        view._error_response(response_arg)

        view._json_response.assert_called_with({
            'status': 403,
            'title': 'U bent niet geautoriseerd voor deze operatie.',
        }, 403)

    @patch("gobstuf.rest.brp.base_view.request")
    def test_not_found_response(self, mock_request):
        mock_request.url = 'REQUEST URL'
        view = StufRestView()
        view._json_response = MagicMock()
        view.get_not_found_message = MagicMock()

        kwargs = {'kw': 'ar', 'g': 's'}

        self.assertEqual(view._json_response.return_value, view._not_found_response(**kwargs))

        view._json_response.assert_called_with({
            'title': 'Opgevraagde resource bestaat niet',
            'status': 404,
            'detail': view.get_not_found_message(),
            'instance': 'REQUEST URL',
            'code': 'notFound'
        }, 404)

    @patch("gobstuf.rest.brp.base_view.request")
    @patch("gobstuf.rest.brp.base_view.StufErrorResponse")
    def test_get(self, mock_response, mock_request):
        mock_request.headers = {
            MKS_USER_HEADER: 'user',
            MKS_APPLICATION_HEADER: 'application',
        }

        class StuffRestViewImpl(StufRestView):
            request_template = MagicMock()
            response_template = MagicMock()

        view = StuffRestViewImpl()
        view._make_request = MagicMock()
        view._error_response = MagicMock()
        view._json_response = MagicMock()

        # Success response
        self.assertEqual(view._json_response.return_value, view.get(a=1, b=2))
        view.request_template.assert_called_with('user', 'application', {'a': 1, 'b': 2})
        view._make_request.assert_called_with(view.request_template.return_value)

        view.response_template.assert_called_with(view._make_request.return_value.text)
        view._json_response.assert_called_with(view.response_template.return_value.get_mapped_object.return_value)

        # Error response
        view._make_request.return_value.raise_for_status.side_effect = HTTPError
        self.assertEqual(view._error_response.return_value, view.get(a=1, b=2))
        mock_response.assert_called_with(view._make_request.return_value.text)
        view._error_response.assert_called_with(mock_response.return_value)

        # 404 response
        view._make_request = MagicMock()
        view.response_template.return_value.get_mapped_object.side_effect = NoStufAnswerException
        view._not_found_response = MagicMock()

        self.assertEqual(view._not_found_response(), view.get(a=1, b=2))
