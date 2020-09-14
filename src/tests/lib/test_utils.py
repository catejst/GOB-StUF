from unittest import TestCase

from gobstuf.lib.utils import get_value

class TestUtils(TestCase):

    def test_get_value(self):
        dict = {
            'a': {
                'b': {
                    'c': 'd'
                }
            }
        }
        self.assertEqual(get_value(dict, 'a', 'b', 'c'), 'd')
        self.assertEqual(get_value(dict, 'a', 'b', 'c', 'd'), None)
