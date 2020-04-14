from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from gobstuf.stuf.message import StufMessage


class StufMessageInitLoadTest(TestCase):
    """
    Tests __init__ and load() methods of StufMessage
    StufMessageTest tests the other methods (and mocks load)
    """

    @patch("gobstuf.stuf.message.StufMessage.set_namespaces")
    @patch("gobstuf.stuf.message.ET.fromstring")
    def test_init(self, mock_from_string, mock_set_namespaces):
        msg = 'the message'
        namespaces = {'name': 'spaces'}

        message = StufMessage(msg, namespaces)
        mock_set_namespaces.assert_not_called()
        self.assertEqual(namespaces, message.namespaces)
        self.assertEqual(mock_from_string.return_value, message.tree)
        mock_from_string.assert_called_with(msg)

        message = StufMessage(msg)
        self.assertIsNone(message.namespaces)
        mock_set_namespaces.assert_called_with(msg)


@patch("gobstuf.stuf.message.StufMessage.load", MagicMock())
class StufMessageTest(TestCase):

    @patch("gobstuf.stuf.message.StringIO")
    @patch("gobstuf.stuf.message.ET")
    def test_set_namespaces(self, mock_et, mock_stringio):
        mock_et.iterparse.return_value = [
            (1, ('prefix1', 'url1')),
            (2, ('prefix2', 'url2')),
            (3, ('prefix3', 'url3')),
        ]
        msg = 'msg'
        mock_stringio.side_effect = lambda x: 'stringio(' + x + ')'

        message = StufMessage('')
        message.set_namespaces(msg)
        mock_et.iterparse.assert_called_with('stringio(msg)', events=['start-ns'])
        mock_et.register_namespace.assert_has_calls([
            call('prefix1', 'url1'),
            call('prefix2', 'url2'),
            call('prefix3', 'url3'),
        ])
        self.assertEqual({
            'prefix1': 'url1',
            'prefix2': 'url2',
            'prefix3': 'url3',
        }, message.namespaces)

    def test_find_elm(self):
        message = StufMessage('')
        message.tree = MagicMock()
        message.namespaces = MagicMock()

        res = message.find_elm('a b c')

        # Recursive return value
        self.assertEqual(message.tree.find().find().find(), res)

        # Recursive calls
        message.tree.find.assert_has_calls([
            call('a', message.namespaces),
            call().find('b', message.namespaces),
            call().find().find('c', message.namespaces),
        ])

    def test_set_elm_value(self):
        message = StufMessage('')
        message.find_elm = MagicMock()
        message.tree = MagicMock()
        message.set_elm_value('some element', 'some value')
        message.find_elm.assert_called_with('some element', None)
        self.assertEqual('some value', message.find_elm().text)

        mocked_tree = MagicMock()
        message.set_elm_value('some element', 'some value', mocked_tree)
        message.find_elm.assert_called_with('some element', mocked_tree)

    def test_get_elm_value(self):
        message = StufMessage('')
        message.find_elm = MagicMock()
        message.tree = MagicMock()
        res = message.get_elm_value('some element')
        message.find_elm.assert_called_with('some element', None)
        self.assertEqual(message.find_elm().text, res)

        mocked_tree = MagicMock()
        message.get_elm_value('some element', mocked_tree)
        message.find_elm.assert_called_with('some element', mocked_tree)

    @patch("gobstuf.stuf.message.ET")
    def test_to_string(self, mock_et):
        message = StufMessage('')
        message.tree = MagicMock()

        self.assertEqual(mock_et.tostring(), message.to_string())
        mock_et.tostring.assert_called_with(message.tree, encoding='unicode')

    @patch("gobstuf.stuf.message.ET")
    @patch("gobstuf.stuf.message.minidom.parseString")
    @patch("gobstuf.stuf.message.os.linesep", "\n")
    def test_pretty_print(self, mock_parsestr, mock_et):
        message = StufMessage('')
        message.tree = MagicMock()

        mock_parsestr().toprettyxml().splitlines.return_value = [
            ' ',
            '\n',
            'A',
            '',
            'B',
            '      \n',
            'C',
        ]

        res = message.pretty_print()
        mock_parsestr.assert_called_with(mock_et.tostring.return_value)
        mock_et.tostring.assert_called_with(message.tree)
        self.assertEqual('A\nB\nC', res)
