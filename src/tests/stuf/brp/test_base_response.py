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

    def test_get_mapped_object(self):
        resp = StufMappedResponseImpl('msg')
        resp.get_object_elm = MagicMock()

        result = resp.get_mapped_object()
        expected = {
            'attr1': resp.stuf_message.get_elm_value(),
            'attr2': resp.stuf_message.get_elm_value(),
        }
        self.assertEqual(expected, result)

        resp.stuf_message.get_elm_value.assert_has_calls([
            call('XML PATH A', resp.get_object_elm()),
            call('XML PATH B', resp.get_object_elm()),
        ])

