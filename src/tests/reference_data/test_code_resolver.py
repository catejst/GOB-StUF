from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError, ConnectionError

from gobstuf.reference_data.code_resolver import CodeResolver, CodeNotFoundException


class TestCodeResolver(TestCase):

    def test_initialize(self):
        # Assert that landen table has been initialised
        self.assertTrue(CodeResolver._landen)

    @patch("builtins.open")
    def test_load_landen(self, mock_open):
        mock_open.side_effect = FileNotFoundError
        with self.assertRaises(CodeNotFoundException):
            CodeResolver._load_landen()

    def test_get_land(self):
        result = CodeResolver.get_land("")
        self.assertIsNone(result)

        result = CodeResolver.get_land(None)
        self.assertIsNone(result)

        result = CodeResolver.get_land("any code")
        self.assertIsNone(result)

        CodeResolver._landen['any code'] = {'omschrijving': 'any land'}
        result = CodeResolver.get_land("any code")
        self.assertEqual(result, 'any land')

        # Pad codes to 4 characters
        CodeResolver._landen['0002'] = {'omschrijving': 'any land'}
        for code in ['2', '02', '002']:
            CodeResolver.get_land(code)
            self.assertIsNone(CodeResolver._landen.get(code))

    def mock_valid_request(self, mock_requests):
        mock_requests.get.return_value.json.return_value = {
            'data': {
                'brkGemeentes': {
                    'edges': [{
                        'node': {
                            'naam': 'any naam'
                        }
                    }]
                }
            }
        }

    def mock_invalid_request(self, mock_requests):
        mock_requests.get.return_value.json.return_value = {}


    @patch('gobstuf.reference_data.code_resolver.requests')
    def test_load_gemeente(self, mock_requests):
        # Code not found
        self.mock_invalid_request(mock_requests)
        with self.assertRaises(CodeNotFoundException):
            result = CodeResolver._load_gemeente('any code')
            self.assertIsNone(result)

        # Code found
        self.mock_valid_request(mock_requests)
        result = CodeResolver._load_gemeente('any code')
        self.assertEqual(result, 'any naam')

        # HTTP or Connection error
        for ex in [HTTPError, ConnectionError]:
            mock_requests.get.side_effect = ex
            with self.assertRaises(CodeNotFoundException):
                result = CodeResolver._load_gemeente('any code')
                self.assertIsNone(result)

    @patch('gobstuf.reference_data.code_resolver.requests')
    def test_get_gemeente(self, mock_requests):
        result = CodeResolver.get_gemeente('')
        self.assertIsNone(result)

        result = CodeResolver.get_gemeente(None)
        self.assertIsNone(result)

        # Return None if code cannot be found
        self.mock_invalid_request(mock_requests)
        result = CodeResolver.get_gemeente('any code')
        self.assertIsNone(result)

        # Return naam if code is valid
        self.mock_valid_request(mock_requests)
        result = CodeResolver.get_gemeente('any code')
        self.assertEqual(result, 'any naam')

        # Use cached value if it exists
        self.mock_invalid_request(mock_requests)
        result = CodeResolver.get_gemeente('any code')
        self.assertEqual(result, 'any naam')

        # Pad codes to 4 characters
        self.mock_valid_request(mock_requests)
        self.assertIsNone(CodeResolver._gemeenten.get('0002'))
        for code in ['2', '02', '002']:
            CodeResolver.get_gemeente(code)
            self.assertIsNone(CodeResolver._gemeenten.get(code))
        self.assertIsNotNone(CodeResolver._gemeenten['0002'])
