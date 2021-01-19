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
        message.set_elm_value('some element', 'some value', exact_match=True, tree=mocked_tree)
        message.find_elm.assert_called_with('some element', mocked_tree)

        # Assert StUF:exact false is set for elements without exact_match to allow for search in MKS
        message.set_elm_value('some element', 'some value*', exact_match=False, tree=mocked_tree)
        element = message.find_elm.return_value
        element.set.assert_called_with('StUF:exact', 'false')
        # Expect the WILDCARD_CHAR to be replaced with the STUF_WILDCARD_CHAR
        self.assertEqual('some value%', message.find_elm().text)

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
        mock_et.tostring.assert_called_with(message.tree, encoding='utf-8')

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
        mock_et.tostring.assert_called_with(message.tree, encoding='utf-8')
        self.assertEqual('A\nB\nC', res)


class TestXML(TestCase):

    def setUp(self) -> None:
        self.msg = '''
<root xmlns:StUF="http://www.egem.nl/StUF/StUF0301">
  <elm1 attr="attr">value</elm1>
  <elm2>
    <elm2sub dummy="dummy value" StUF:attr="ns2 attr">sub value</elm2sub>
  </elm2>
  <elm3>
    <elm3sub>
      <sub x="1">sub1</sub>
      <sub x="3">sub3</sub>
      <sub x="2">sub2</sub>
    </elm3sub>
  </elm3>
  <elm4 />
  <elm8>
    <elm8sub>1</elm8sub> 
    <elm8sub>2</elm8sub> 
    <elm8sub>3</elm8sub> 
  </elm8>
  <elm8>
    <elm8sub>4</elm8sub> 
    <elm8sub>5</elm8sub> 
  </elm8>
</root>
'''

    def test_get_elm_attr(self):
        stuf = StufMessage(self.msg)

        # Get a root element
        e = stuf.get_elm_value('elm1')
        self.assertEqual(e, 'value')

        # Get an element at a sub level
        e = stuf.get_elm_value('elm2 elm2sub')
        self.assertEqual(e, 'sub value')

        # Get a root element that does not exist
        e = stuf.get_elm_value('unknown')
        self.assertEqual(e, None)

        # Get an attribute
        e = stuf.get_elm_attr('elm1', 'attr')
        self.assertEqual(e, 'attr')

        # Get an attribute at a sub level
        e = stuf.get_elm_attr('elm2 elm2sub', 'dummy')
        self.assertEqual(e, 'dummy value')

        # Get a namespace attribute
        e = stuf.get_elm_attr('elm2 elm2sub', 'StUF:attr')
        self.assertEqual(e, 'ns2 attr')

        # Get an attribute that does not exist
        e = stuf.get_elm_attr('elm1', 'unkown')
        self.assertEqual(e, None)

        e = stuf.get_elm_value_by_path("elm3", ".//elm3sub//sub[@x='3']")
        self.assertEqual(e, 'sub3')

        e = stuf.get_elm_value_by_path("elm3", ".//elm3sub//sub[@x='5']")
        self.assertEqual(e, None)

    def test_create_elm(self):
        stuf_message = StufMessage(self.msg)

        elm = 'elm4 elm5 elm6'

        stuf_message.create_elm(elm)
        stuf_message.set_elm_value(elm, 'value of new elm6')

        self.assertEqual('value of new elm6', stuf_message.get_elm_value(elm))
        self.assertEqual("""<?xml version="1.0" ?>
<root xmlns:StUF="http://www.egem.nl/StUF/StUF0301">
	<elm1 attr="attr">value</elm1>
	<elm2>
		<elm2sub dummy="dummy value" StUF:attr="ns2 attr">sub value</elm2sub>
	</elm2>
	<elm3>
		<elm3sub>
			<sub x="1">sub1</sub>
			<sub x="3">sub3</sub>
			<sub x="2">sub2</sub>
		</elm3sub>
	</elm3>
	<elm4>
		<elm5>
			<elm6>value of new elm6</elm6>
		</elm5>
	</elm4>
	<elm8>
		<elm8sub>1</elm8sub>
		<elm8sub>2</elm8sub>
		<elm8sub>3</elm8sub>
	</elm8>
	<elm8>
		<elm8sub>4</elm8sub>
		<elm8sub>5</elm8sub>
	</elm8>
</root>""", stuf_message.pretty_print())

        # Already exists. Original value should be returned
        stuf_message.create_elm('elm1')
        self.assertEqual('value', stuf_message.get_elm_value('elm1'))

        # Create element in root
        stuf_message.create_elm('elm7')
        stuf_message.set_elm_value('elm7', 'elm7value')
        self.assertEqual('elm7value', stuf_message.get_elm_value('elm7'))

        # Try to create element with namespace
        stuf_message.create_elm('elm9 StUF:elm10')
        stuf_message.set_elm_value('elm9 StUF:elm10', 'the value')
        self.assertEqual('the value', stuf_message.get_elm_value('elm9 StUF:elm10'))

    def test_find_all_elms(self):
        stuf_message = StufMessage(self.msg)

        self.assertEqual([], stuf_message.find_all_elms('elm1 elm2'))
        self.assertEqual([], stuf_message.find_all_elms('nonexistent'))

        # Triggers case where parent path is not found
        self.assertEqual([], stuf_message.find_all_elms('non existent'))

        self.assertEqual(3, len(stuf_message.find_all_elms('elm3 elm3sub sub')))
        self.assertEqual([
            'sub1',
            'sub3',
            'sub2',
        ], [elm.text for elm in stuf_message.find_all_elms('elm3 elm3sub sub')])

        # Only elements from first elm8 should be returned
        self.assertEqual([
            '1',
            '2',
            '3',
        ], [elm.text for elm in stuf_message.find_all_elms('elm8 elm8sub')])
