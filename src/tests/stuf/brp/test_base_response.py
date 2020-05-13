from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from gobstuf.stuf.brp.base_response import StufResponse, StufMappedResponse, NoStufAnswerException, Mapping, \
    MappedObjectWrapper


@patch("gobstuf.stuf.brp.base_response.StufMessage")
class StufResponseTest(TestCase):

    def test_stuf_response(self, mock_stuf_message):
        resp = StufResponse('msg', kwarg1='value1')

        self.assertEqual(resp.stuf_message, mock_stuf_message())
        mock_stuf_message.assert_any_call('msg', resp.namespaces)

        self.assertEqual(mock_stuf_message().pretty_print(), resp.to_string())
        self.assertEqual('value1', resp.kwarg1)


class StufMappedResponseImpl(StufMappedResponse):
    answer_section = 'ANSWER SECTION'
    object_elm = 'OBJECT'

    class MockMapping(Mapping):
        entity_type = 'TST'
        mapping = {
            'attr1': 'XML PATH A',
            'attr2': 'XML PATH B',
            'attr3': {
                'attr3a': 'XML PATH C - a',
                'attr3b': 'XML PATH C - b'
            },
            'attr4': (len, 'XML PATH D'),
            'attr5': '=attr5 value',
            'attr6': 'XML PATH E@ATTR',
            'attr7': 'XML PATH F!XPATH EXPRESSION'
        }

        def filter(self, obj, **kwargs):
            return obj

    def _get_mapping(self, *args):
        return self.MockMapping()


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

    def test_get_all_object_elms(self):
        resp = StufMappedResponseImpl('msg')
        result = resp.get_all_object_elms()
        self.assertEqual(resp.stuf_message.find_all_elms.return_value, result)
        resp.stuf_message.find_all_elms.assert_called_with('ANSWER SECTION OBJECT')

    def _get_expected_mapped_result(self, resp):
        mapping = resp._get_mapping(None).mapping
        return {
            'attr1': resp.stuf_message.get_elm_value(mapping['attr1']),
            'attr2': resp.stuf_message.get_elm_value(mapping['attr2']),
            'attr3': {
                'attr3a': resp.stuf_message.get_elm_value(mapping['attr3']['attr3a']),
                'attr3b': resp.stuf_message.get_elm_value(mapping['attr3']['attr3b']),
            },
            'attr4': len(resp.stuf_message.get_elm_value(mapping['attr4'][1])),
            'attr5': 'attr5 value',
            'attr6': resp.stuf_message.get_elm_attr(mapping['attr6'], 'ATTR'),
            'attr7': 'xpath XPATH EXPRESSION'
        }

    def _mock_stuf_message(self, resp):
        resp.get_object_elm = MagicMock()
        resp.stuf_message.get_elm_value = lambda a, o=None: f"value {a}"
        resp.stuf_message.get_elm_attr = lambda a, attr, o=None: f"attr {attr}"
        resp.stuf_message.get_elm_value_by_path = lambda a, path, o=None: f"xpath {path}"

    def test_get_links(self):
        resp = StufMappedResponseImpl('msg')
        self.assertEqual(resp.get_links({'any': 'data'}), {})

    def test_get_filter_kwargs(self):
        resp = StufMappedResponseImpl('msg')
        resp.filter_kwargs = ['a', 'b', 'c']
        resp.a = 'A'
        resp.b = 'B'
        self.assertEqual({'a': 'A', 'b': 'B', 'c': None}, resp._get_filter_kwargs())

    def test_get_answer_object(self):
        resp = StufMappedResponseImpl('msg')
        self._mock_stuf_message(resp)

        result = resp.get_answer_object()
        self.assertEqual(result, self._get_expected_mapped_result(resp))

    def test_get_answer_object_no_answer(self):
        resp = StufMappedResponseImpl('msg')
        resp.get_mapped_object = lambda: type('MockObj', (), {'get_filtered_object': lambda: None})

        with self.assertRaises(NoStufAnswerException):
            result = resp.get_answer_object()

    def test_get_all_answer_objects(self):
        class MockMappedObj:
            def __init__(self, mockname):
                self.mockname = mockname

            def get_filtered_object(self):
                return 'filtered ' + self.mockname

        resp = StufMappedResponseImpl('msg')
        resp.get_all_object_elms = MagicMock(return_value=['object A', 'object B'])
        resp.get_mapped_object = lambda x: MockMappedObj('mapped ' + x)
        resp.get_filtered_object = lambda x: 'filtered ' + x
        self.assertEqual([
            'filtered mapped object A',
            'filtered mapped object B',
        ], resp.get_all_answer_objects())

    @patch("gobstuf.stuf.brp.base_response.StufObjectMapping.get_for_entity_type")
    def test_get_mapping(self, mock_get_for_entity_type):

        class Impl(StufMappedResponse):
            answer_section = 'ANSWER SECTION'
            object_elm = 'OBJECT'

        resp = Impl('msg')

        element = type('MockElement', (), {'attrib': {
            '{http://www.egem.nl/StUF/StUF0301}entiteittype': 'TST'
        }})

        self.assertEqual(mock_get_for_entity_type.return_value, resp._get_mapping(element))
        mock_get_for_entity_type.assert_called_with('TST')

