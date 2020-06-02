from unittest import TestCase

from gobstuf.stuf.brp.request.ingeschrevenpersonen import IngeschrevenpersonenFilterStufRequest


class TestIngeschrevenPersonenFilterStufRequest(TestCase):

    def test_convert_param_geboorte__datum(self):
        request = IngeschrevenpersonenFilterStufRequest('gebruiker', 'applicatie')

        self.assertEqual('20200528', request.convert_param_geboorte__datum('2020-05-28'))

        with self.assertRaises(AssertionError):
            request.convert_param_geboorte__datum('INVALID')

