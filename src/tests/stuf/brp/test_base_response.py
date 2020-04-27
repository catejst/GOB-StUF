from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from gobstuf.stuf.brp.base_response import StufResponse, StufMappedResponse, NoStufAnswerException


@patch("gobstuf.stuf.brp.base_response.StufMessage")
class StufResponseTest(TestCase):

    def test_stuf_response(self, mock_stuf_message):
        resp = StufResponse('msg')

        self.assertEqual(resp.stuf_message, mock_stuf_message())
        mock_stuf_message.assert_any_call('msg', resp.namespaces)

        self.assertEqual(mock_stuf_message().pretty_print(), resp.to_string())


class StufMappedResponseImpl(StufMappedResponse):
    answer_section = 'ANSWER SECTION'
    object_elm = 'OBJECT'
    mapping = {
        'attr1': 'XML PATH A',
        'attr2': 'XML PATH B',
        'attr3': {
            'attr3a': 'XML PATH C - a',
            'attr3b': 'XML PATH C - b'
        },
        'attr4': (len, 'XML PATH D'),
        'attr5': '=attr5 value'
    }


@patch("gobstuf.stuf.brp.base_response.StufMessage", MagicMock())
class StufMappedResponseTest(TestCase):

    def test_get_object_elm(self):
        resp = StufMappedResponseImpl('msg')

        result = resp.get_object_elm()
        self.assertEqual(resp.stuf_message.find_elm.return_value, result)

        # Test exception
        resp.stuf_message.find_elm.return_value = None

        with self.assertRaises(NoStufAnswerException):
            resp.get_object_elm()

    def _get_expected_mapped_result(self, resp):
        return {
            'attr1': resp.stuf_message.get_elm_value(resp.mapping['attr1']),
            'attr2': resp.stuf_message.get_elm_value(resp.mapping['attr2']),
            'attr3': {
                'attr3a': resp.stuf_message.get_elm_value(resp.mapping['attr3']['attr3a']),
                'attr3b': resp.stuf_message.get_elm_value(resp.mapping['attr3']['attr3b']),
            },
            'attr4': len(resp.stuf_message.get_elm_value(resp.mapping['attr4'][1])),
            'attr5': 'attr5 value'
        }

    def test_get_links(self):
        resp = StufMappedResponseImpl('msg')
        self.assertEqual(resp.get_links(), {})

    def test_get_mapped_object(self):
        resp = StufMappedResponseImpl('msg')
        resp.get_object_elm = MagicMock()
        resp.stuf_message.get_elm_value = lambda a, o=None: f"value {a}"

        result = resp.get_mapped_object()
        self.assertEqual(result, self._get_expected_mapped_result(resp))

    def test_get_answer_object(self):
        resp = StufMappedResponseImpl('msg')
        resp.get_object_elm = MagicMock()

        result = resp.get_answer_object()
        self.assertEqual(result, self._get_expected_mapped_result(resp))

        resp.get_filtered_object = MagicMock()
        resp.get_filtered_object.return_value = None
        with self.assertRaises(NoStufAnswerException):
            result = resp.get_answer_object()

    def test_get_filtered_object(self):
        resp = StufMappedResponseImpl('msg')
        obj = {
            'any key': 'any value',
            'any null': None,
            'sub': {
                'any sub key': 'any sub value',
                'any sub null': None,
                'sub sub1': {
                    'any sub sub null': None
                },
                'sub sub2': {
                    'any sub sub': 'any sub sub value'
                }
            }
        }
        expect = {
            'any key': 'any value',
            'sub': {
                'any sub key': 'any sub value',
                'sub sub2': {
                    'any sub sub': 'any sub sub value'
                }
            }
        }
        # Default filtering is return all non null values
        self.assertEqual(resp.get_filtered_object(obj), expect)
