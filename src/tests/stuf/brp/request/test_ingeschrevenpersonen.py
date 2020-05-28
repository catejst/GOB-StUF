from unittest import TestCase

from gobstuf.stuf.brp.request.ingeschrevenpersonen import IngeschrevenpersonenFilterStufRequest


class TestIngeschrevenPersonenFilterStufRequest(TestCase):

    def test_convert_param_geboorte__datum(self):
        request = IngeschrevenpersonenFilterStufRequest('gebruiker', 'applicatie')

        self.assertEqual('20200528', request.convert_param_geboorte__datum('2020-05-28'))

        with self.assertRaises(AssertionError):
            request.convert_param_geboorte__datum('INVALID')

    # def test_validate(self):
    #     request = IngeschrevenpersonenFilterStufRequest('gebruiker', 'applicatie')
    #
    #     result = request.validate({'geboorte__datum': '2000-02-28'})
    #     self.assertIsNone(result)
    #
    #     result = request.validate({'geboorte__datum': '2000-02-30'})
    #     self.assertEqual(result['invalid-params'], [{
    #         'code': 'invalidDate',
    #         'reason': 'Ongeldige datum opgegeven',
    #         'name': 'geboorte__datum'
    #     }])
    #
    #     result = request.validate({'geboorte__datum': '2000-0229'})
    #     self.assertEqual(result['invalid-params'], [{
    #         'code': 'invalidFormat',
    #         'reason': 'Waarde voldoet niet aan het formaat YYYY-MM-DD',
    #         'name': 'geboorte__datum'
    #     }])
    #
    #     result = request.validate({'naam__geslachtsnaam': 'Gage'})
    #     self.assertIsNone(result)
    #
    #     result = request.validate({'naam__geslachtsnaam': 'Mannix' * 100})
    #     self.assertEqual(result['invalid-params'], [{
    #         'code': 'maxLength',
    #         'reason': 'Waarde is langer dan maximale lengte 200',
    #         'name': 'naam__geslachtsnaam',
    #     }])
    #
    #
