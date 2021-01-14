from unittest import TestCase, mock
from unittest.mock import patch, MagicMock

from gobstuf.auth.routes import secure_route, _get_roles, get_auth_url, \
                                MKS_USER_KEY, USER_NAME_HEADER, _allows_access, _get_role


class MockRequest():
    pass

mock_request = MockRequest()


class MockG():
    def __init__(self):
        self.__setattr__(MKS_USER_KEY, None)

mock_g = MockG()


class TestAuth(TestCase):

    @patch("gobstuf.auth.routes.is_secured_request")
    @patch("gobstuf.auth.routes._allows_access")
    def test_secure_route(self, mock_allows_access, mock_is_secured_request):
        mock_request = MagicMock()
        func = lambda *args, **kwargs: "Any result"
        wrapped_func = secure_route("any rule", func)

        with patch("gobstuf.auth.routes.request", mock_request):

            mock_allows_access.return_value = False
            mock_is_secured_request.return_value = True
            self.assertEqual(("Forbidden", 403), wrapped_func())

            mock_allows_access.return_value = True
            mock_is_secured_request.return_value = False
            self.assertEqual(("Forbidden", 403), wrapped_func())

            mock_allows_access.return_value = False
            mock_is_secured_request.return_value = False
            self.assertEqual(("Forbidden", 403), wrapped_func())

            mock_allows_access.return_value = True
            mock_is_secured_request.return_value = True
            self.assertEqual("Any result", wrapped_func(1, kw=2))

            mock_is_secured_request.assert_called_with(mock_request.headers)
            mock_allows_access.assert_called_with("any rule", 1, kw=2)

    @patch('gobstuf.auth.routes.extract_roles')
    def test_get_roles(self, mock_extract_roles):
        with patch('gobstuf.auth.routes.request', mock_request):
            mock_request.headers = {'some': 'header'}
            mock_extract_roles.return_value = ['any role', 'another role']
            self.assertEqual(_get_roles(), ['any role', 'another role'])
            mock_extract_roles.assert_called_with(mock_request.headers)

            delattr(mock_request, 'headers')
            self.assertEqual(_get_roles(), [])

    @patch('gobstuf.auth.routes._get_roles')
    def test_get_role(self, mock_get_roles):
        mock_get_roles.return_value = []
        self.assertIsNone(_get_role())

        mock_get_roles.return_value = ['some ignored role']
        self.assertIsNone(_get_role())

        mock_get_roles.return_value = ['some ignored role', 'fp_the_role']
        self.assertEqual('fp_the_role', _get_role())

        mock_get_roles.return_value = ['some ignored role', 'fp_the_role', 'fp_other_role']
        self.assertEqual('fp_the_role', _get_role())

    @patch('gobstuf.auth.routes._get_role')
    def test_allows_access(self, mock_get_role):
        mock_g = MagicMock()
        mock_request = MagicMock()

        with patch('gobstuf.auth.routes.g', mock_g), \
            patch('gobstuf.auth.routes.request', mock_request):
                mock_get_role.return_value = None
                mock_request.headers = {USER_NAME_HEADER: 'some username'}
                self.assertFalse(_allows_access('rule'))

                mock_get_role.return_value = 'some role'
                self.assertTrue(_allows_access('rule'))
                self.assertEqual('some role', mock_g.MKS_APPLICATIE)
                self.assertEqual('some username', mock_g.MKS_GEBRUIKER)

    @patch('gobstuf.auth.routes.url_for')
    def test_get_auth_url(self, mock_url_for):
        mock_request = MagicMock()

        with patch('gobstuf.auth.routes.request', mock_request):
            view_name = 'any view'
            mock_request.scheme = 'http(s)'
            mock_request.host = 'any host'
            mock_request.base_url = ''

            mock_url_for.return_value = '/any url'

            result = get_auth_url(view_name)
            self.assertEqual(result, "http(s)://any host/any url")
            mock_url_for.assert_called_with('any view')
