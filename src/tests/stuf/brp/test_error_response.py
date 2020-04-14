from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.stuf.brp.error_response import StufErrorResponse


@patch("gobstuf.stuf.brp.error_response.StufResponse.load", MagicMock())
class TestErrorResponse(TestCase):

    def test_get_error_code(self):
        response = StufErrorResponse('')
        response.stuf_message = MagicMock()
        response.stuf_message.find_elm.return_value = iter(['a', 'b'])

        self.assertEqual(response.stuf_message.get_elm_value.return_value, response.get_error_code())

        response.stuf_message.get_elm_value.assert_called_with('StUF:stuurgegevens StUF:berichtcode', 'a')

    def test_get_error_string(self):
        response = StufErrorResponse('')
        response.stuf_message = MagicMock()

        self.assertEqual(response.stuf_message.get_elm_value.return_value, response.get_error_string())
        response.stuf_message.get_elm_value.assert_called_with(response.string_path)
