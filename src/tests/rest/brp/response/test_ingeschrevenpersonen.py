from unittest import TestCase

from gobstuf.stuf.brp.response.ingeschrevenpersonen import IngeschrevenpersonenStufResponse


class TestIngeschrevenpersonenStufResponse(TestCase):

    def test_get_filtered_object(self):
        res = IngeschrevenpersonenStufResponse(b'<xml></xml>')

        obj = {}
        result = res.get_filtered_object(obj)
        self.assertEqual(result, {})

        obj = {'any key': 'any value'}
        result = res.get_filtered_object(obj)
        self.assertEqual(result, obj)

        obj = {'any key': 'any value', 'overlijdensdatum': 'any datum'}
        result = res.get_filtered_object(obj)
        self.assertEqual(result, None)

        res.inclusiefoverledenpersonen = True
        result = res.get_filtered_object(obj)
        self.assertEqual(result, obj)
