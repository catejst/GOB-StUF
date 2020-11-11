from unittest import TestCase, mock
from unittest.mock import patch, MagicMock

from gobstuf.auth.routes import secure_route, _get_roles, get_auth_url, \
                                REQUIRED_ROLE_PREFIX, MKS_USER_KEY, MKS_APPLICATION_KEY
from gobcore.secure.config import REQUEST_USER, REQUEST_ROLES


class MockRequest():
    pass

mock_request = MockRequest()


class MockG():
    def __init__(self):
        self.__setattr__(MKS_USER_KEY, None)

mock_g = MockG()


class TestAuth(TestCase):

    @patch('gobstuf.auth.routes.g', mock_g)
    @patch('gobstuf.auth.routes.request', mock_request)
    def test_secure_route(self):
        func = lambda *args, **kwargs: "Any result"

        wrapped_func = secure_route("any rule", func)

        mock_request.headers = {}
        result = wrapped_func()
        self.assertEqual(result, (mock.ANY, 403))

        mock_request.headers = {
            REQUEST_USER: "any user"
        }
        result = wrapped_func()
        self.assertEqual(result, (mock.ANY, 403))

        mock_request.headers = {
            REQUEST_ROLES: "any role"
        }
        result = wrapped_func()
        self.assertEqual(result, (mock.ANY, 403))

        mock_request.headers = {
            REQUEST_USER: "any user",
            REQUEST_ROLES: "any role"
        }
        result = wrapped_func()
        self.assertEqual(result, (mock.ANY, 403))

        # A role with 'fp_' is required
        mock_request.headers = {
            REQUEST_USER: "any user",
            REQUEST_ROLES: f"{REQUIRED_ROLE_PREFIX}any role"
        }
        result = wrapped_func()
        self.assertEqual(result, "Any result")
        self.assertEqual(getattr(mock_g, MKS_APPLICATION_KEY), "fp_any role")
        self.assertEqual(getattr(mock_g, MKS_USER_KEY), "any user")

    @patch('gobstuf.auth.routes.request', mock_request)
    def test_get_roles(self):
        mock_request.headers = {
            REQUEST_ROLES: f"any role,another role"
        }
        self.assertEqual(_get_roles(), ['any role', 'another role'])

        mock_request.headers = {}
        self.assertEqual(_get_roles(), [])

        delattr(mock_request, 'headers')
        self.assertEqual(_get_roles(), [])

    @patch('gobstuf.auth.routes.request')
    @patch('gobstuf.auth.routes.url_for')
    def test_get_auth_url(self, mock_url_for, mock_request):
        view_name = 'any view'
        mock_request.scheme = 'http(s)'
        mock_request.host = 'any host'
        mock_request.base_url = ''

        mock_url_for.return_value = '/any url'

        result = get_auth_url(view_name)
        self.assertEqual(result, "http(s)://any host/any url")
        mock_url_for.assert_called_with('any view')
