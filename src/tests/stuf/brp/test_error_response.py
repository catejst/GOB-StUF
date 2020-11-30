from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.stuf.brp.error_response import StufErrorResponse, UnknownErrorCode


@patch("gobstuf.stuf.brp.error_response.StufResponse.load", MagicMock())
class TestErrorResponse(TestCase):

    def test_get_value_methods(self):
        response = StufErrorResponse('')
        response.stuf_message = MagicMock()
        response.stuf_message.find_elm = lambda x: iter(['a', 'b'])

        self.assertEqual(response.stuf_message.get_elm_value.return_value, response.get_error_code())
        response.stuf_message.get_elm_value.assert_called_with('StUF:body StUF:code', 'a')

        self.assertEqual(response.stuf_message.get_elm_value.return_value, response.get_error_plek())
        response.stuf_message.get_elm_value.assert_called_with('StUF:body StUF:plek', 'a')

        self.assertEqual(response.stuf_message.get_elm_value.return_value, response.get_error_omschrijving())
        response.stuf_message.get_elm_value.assert_called_with('StUF:body StUF:omschrijving', 'a')

        self.assertEqual(response.stuf_message.get_elm_value.return_value, response.get_berichtcode())
        response.stuf_message.get_elm_value.assert_called_with('StUF:stuurgegevens StUF:berichtcode', 'a')

    @patch("gobstuf.stuf.brp.error_response.RESTResponse")
    def test_get_http_response(self, mock_rest_response):
        response = StufErrorResponse('')
        response.get_berichtcode = MagicMock(return_value='something else')

        with self.assertRaises(UnknownErrorCode):
            response.get_http_response()

        response.get_berichtcode.return_value = 'Fo02'
        response.get_error_code = MagicMock()

        for i in range(1, 14):
            response.get_error_code.return_value = f"StUF{i:03}"

            # No exceptions
            response.get_http_response()

        response.get_error_code.return_value = f"StUFUnknown"

        with self.assertRaises(UnknownErrorCode):
            response.get_http_response()
