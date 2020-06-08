from unittest import TestCase
from unittest.mock import patch

from gobstuf.stuf.brp.request.ingeschrevenpersonen import IngeschrevenpersonenFilterStufRequest


class TestIngeschrevenPersonenFilterStufRequest(TestCase):

    def test_convert_param_geboorte__datum(self):
        request = IngeschrevenpersonenFilterStufRequest('gebruiker', 'applicatie')

        self.assertEqual('20200528', request.convert_param_geboorte__datum('2020-05-28'))

        with self.assertRaises(AssertionError):
            request.convert_param_geboorte__datum('INVALID')

    @patch('gobstuf.stuf.brp.request.ingeschrevenpersonen.CodeResolver')
    def test_convert_param_verblijfplaats__gemeentevaninschrijving(self, mock_code_resolver):
        mock_code_resolver.get_gemeente_code.return_value = '0363'
        request = IngeschrevenpersonenFilterStufRequest('gebruiker', 'applicatie')

        self.assertEqual('363', request.convert_param_verblijfplaats__gemeentevaninschrijving('Amsterdam'))
