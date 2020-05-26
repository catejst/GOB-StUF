from unittest import TestCase

from gobstuf.stuf.brp.request.ingeschrevenpersonen import IngeschrevenpersonenBsnStufRequest, IngeschrevenpersonenFilterStufRequest

class TestIngeschrevenpersonenStufRequest(TestCase):

    def test_validate(self):
        req = IngeschrevenpersonenBsnStufRequest("gebruiker", "applicatie", {'bsn': 'any bsn'})

        for bsn in ['', '12345', '1234567']:
            result = req.validate({'bsn': bsn})
            self.assertEqual(result['invalid-params'], [{
                'code': 'minLength',
                'reason': f'Waarde is korter dan minimale lengte {req.BSN_LENGTH}.',
                'name': 'burgerservicenummer'
            }])
        self.assertTrue('burgerservicenummer' in result['detail'])

        for bsn in ['1234567890', '12345678901']:
            result = req.validate({'bsn': bsn})
            self.assertEqual(result['invalid-params'], [{
                'code': 'maxLength',
                'reason': f'Waarde is langer dan maximale lengte {req.BSN_LENGTH}.',
                'name': 'burgerservicenummer'
            }])

        result = req.validate({'bsn': '123456789'})
        self.assertEqual(result, None)

        req = IngeschrevenpersonenFilterStufRequest("gebruiker", "applicatie", {'burgerservicenummer': 'any bsn'})
        for bsn in ['12345', '1234567']:
            result = req.validate({'burgerservicenummer': bsn})
            self.assertEqual(result['invalid-params'], [{
                'code': 'minLength',
                'reason': f'Waarde is korter dan minimale lengte {req.BSN_LENGTH}.',
                'name': 'burgerservicenummer'
            }])
        self.assertTrue('burgerservicenummer' in result['detail'])

        for bsn in ['1234567890', '12345678901']:
            result = req.validate({'burgerservicenummer': bsn})
            self.assertEqual(result['invalid-params'], [{
                'code': 'maxLength',
                'reason': f'Waarde is langer dan maximale lengte {req.BSN_LENGTH}.',
                'name': 'burgerservicenummer'
            }])

        result = req.validate({'burgerservicenummer': '123456789'})
        self.assertEqual(result, None)
