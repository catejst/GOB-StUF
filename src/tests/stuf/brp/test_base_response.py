from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from gobstuf.stuf.brp.base_response import StufResponse, StufMappedResponse, NoStufAnswerException, Mapping, \
    MappedObjectWrapper, RelatedDetailResponse, RelatedListResponse
from gobstuf.stuf.brp.response_mapping import RelatedMapping


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
            'attr7': 'XML PATH F!XPATH EXPRESSION',
            'attr8': ['XML PATH A', 'attr']
        }

        def filter(self, obj, **kwargs):
            return obj

        def get_links(self, mapped_object) -> dict:
            return {
                'self': {
                    'href': 'http://path/to/me'
                }
            }

    def _get_mapping(self, *args):
        return self.MockMapping()


class MockRelatedResponse(MagicMock):
    related_type = 'relation'


class StufMappedResponseRelatedImpl(StufMappedResponseImpl):
    response_type = MockRelatedResponse()


class MappedObjectWrapperTest(TestCase):
    class MockMapping(Mapping):
        entity_type = 'TST'
        mapping = {
            'A': 'some mapping to A',
            'B': 'some mapping to B',
            'C': 'some mapping to C',
        }

        def get_links(self, mapped_object) -> dict:
            return {
                'linkToB': f'http://host/path/to/{mapped_object["B"]}'
            }

        def filter(self, mapped_object: dict, **kwargs):
            # Simple filter function that assures kwargs is passed correctly
            keep = ['A'] + kwargs.get('keep_too', [])
            return {k: v for k, v in mapped_object.items() if k in keep}

    class MockMappingFilterNone(MockMapping):
        # Should of class above. Mimicks filtered out object.
        def filter(self, mapped_object: dict, **kwargs):
            return None

    def test_get_filtered_object(self):
        mapped_object = {
            'A': 'some value for A',
            # B will be filtered out by the MockMapping class, but not before creating the link to B.
            'B': 'idForB',
            'C': 'some value for C',
        }

        wrapper = MappedObjectWrapper(mapped_object, self.MockMapping(), MagicMock())
        result = wrapper.get_filtered_object(keep_too=['C'])

        # If this succeeds, we are certain that:
        # - The kwargs to get_filtered_object are passed correctly to the filter() method of the mapping class
        # - get_links() is called before filter() (otherwise linkToB would fail)
        expected = {
            'A': 'some value for A',
            'C': 'some value for C',
            '_links': {
                'linkToB': 'http://host/path/to/idForB'
            }
        }
        self.assertEqual(expected, result)

        # Handle None case
        wrapper = MappedObjectWrapper(mapped_object, self.MockMappingFilterNone(), MagicMock())
        self.assertIsNone(wrapper.get_filtered_object())


@patch("gobstuf.stuf.brp.base_response.StufMessage", MagicMock())
class StufMappedResponseTest(TestCase):

    @patch("gobstuf.stuf.brp.base_response.RelatedListResponse", MockRelatedResponse)
    def test_init(self):
        resp = StufMappedResponseImpl('msg', expand='a,b')
        self.assertEqual(['a', 'b'], resp.expand)

        resp = StufMappedResponseImpl('msg', expand=None)
        self.assertEqual([], resp.expand)

        # When a RelatedDetailResponse or RelatedListResponse is defined, expect the relation to be in the expand list
        resp = StufMappedResponseRelatedImpl('msg', expand=None)
        self.assertEqual(['relation'], resp.expand)

        resp = StufMappedResponseImpl('msg')
        self.assertEqual([], resp.expand)

    def test_get_object_elm(self):
        resp = StufMappedResponseImpl('msg')
        resp.stuf_message.find_elm.return_value = MagicMock()

        result = resp.get_object_elm()
        self.assertEqual(resp.stuf_message.find_elm.return_value, result)

        # Test exception
        resp.stuf_message.find_elm.return_value = None

        with self.assertRaises(NoStufAnswerException):
            resp.get_object_elm()

    def test_get_all_object_elms(self):
        resp = StufMappedResponseImpl('msg')
        resp.stuf_message.find_all_elms = MagicMock()
        result = resp.get_all_object_elms()
        self.assertEqual(resp.stuf_message.find_all_elms.return_value, result)
        resp.stuf_message.find_all_elms.assert_called_with('ANSWER SECTION OBJECT')

    def _get_expected_mapped_result(self, resp):
        mapping = resp._get_mapping(None).mapping
        return {
            '_embedded': {},
            '_links': {
                'self': {
                    'href': 'http://path/to/me'
                }
            },
            'attr1': resp.stuf_message.get_elm_value(mapping['attr1']),
            'attr2': resp.stuf_message.get_elm_value(mapping['attr2']),
            'attr3': {
                'attr3a': resp.stuf_message.get_elm_value(mapping['attr3']['attr3a']),
                'attr3b': resp.stuf_message.get_elm_value(mapping['attr3']['attr3b']),
            },
            'attr4': len(resp.stuf_message.get_elm_value(mapping['attr4'][1])),
            'attr5': 'attr5 value',
            'attr6': resp.stuf_message.get_elm_attr(mapping['attr6'], 'ATTR'),
            'attr7': 'xpath XPATH EXPRESSION',
            'attr8': []
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

    def test_add_embedded_objects(self):
        class MockedMapping(Mapping):
            entity_type = 'ENT'
            mapping = {}
            related = {
                'partners': 'SOME PATH TO PARTNERS',
                'ouders': 'SOME OTHER PATH TO OUDERS',
            }

        resp = StufMappedResponseImpl('msg')
        resp.expand = ['partners']
        resp.stuf_message.find_all_elms = lambda x, y: x
        resp.create_objects_from_elements = lambda x: 'THE OBJECTS AT ' + x

        mapped_object = MappedObjectWrapper({}, MockedMapping(), 'some element')
        resp._add_embedded_objects(mapped_object)

        self.assertEqual({
            '_embedded': {
                'partners': 'THE OBJECTS AT SOME PATH TO PARTNERS',
            }
        }, mapped_object.mapped_object)

    def test_get_answer_object(self):
        resp = StufMappedResponseImpl('msg')
        resp.get_object_elm = MagicMock()
        resp.create_object_from_element = MagicMock()

        result = resp.get_answer_object()
        self.assertEqual(resp.create_object_from_element.return_value, result)
        resp.create_object_from_element.assert_called_with(resp.get_object_elm.return_value)

    def test_get_answer_object_integrated(self):
        resp = StufMappedResponseImpl('msg')
        self._mock_stuf_message(resp)

        result = resp.get_answer_object()
        self.assertEqual(result, self._get_expected_mapped_result(resp))

    def test_get_answer_object_no_answer(self):
        resp = StufMappedResponseImpl('msg')
        resp.get_object_elm = MagicMock()
        resp.create_object_from_element = MagicMock(return_value=None)

        with self.assertRaises(NoStufAnswerException):
            result = resp.get_answer_object()

    def test_get_answer_object_related(self):
        resp = StufMappedResponseRelatedImpl('msg')
        resp.get_object_elm = MagicMock()
        resp.create_object_from_element = MagicMock()

        result = resp.get_answer_object()
        self.assertEqual(resp.response_type.filter_response.return_value, result)
        resp.create_object_from_element.assert_called_with(resp.get_object_elm.return_value)

    def test_create_object_from_element(self):
        resp = StufMappedResponseImpl('msg')
        resp.get_mapped_object = MagicMock()
        resp._add_embedded_objects = MagicMock()
        resp._get_filter_kwargs = lambda: {'a': 1, 'b': 2}

        self.assertEqual(resp.get_mapped_object().get_filtered_object(),
                         resp.create_object_from_element('Element'))
        resp.get_mapped_object.assert_called_with('Element')
        resp.get_mapped_object().get_filtered_object.assert_called_with(a=1, b=2)
        resp._add_embedded_objects.assert_called_once()

        resp.get_mapped_object.return_value = None
        self.assertIsNone(resp.create_object_from_element('Element'))

    def test_create_objects_from_elements(self):
        resp = StufMappedResponseImpl('msg')
        resp.create_object_from_element = MagicMock(side_effect=lambda x: 'object ' + x if x in ('A', 'B') else None)

        result = resp.create_objects_from_elements(['A', 'B', 'C'])
        self.assertEqual(['object A', 'object B'], result)

    def test_get_all_answer_objects(self):
        resp = StufMappedResponseImpl('msg')
        resp.get_all_object_elms = MagicMock()
        resp.create_objects_from_elements = MagicMock()

        self.assertEqual(resp.create_objects_from_elements.return_value, resp.get_all_answer_objects())
        resp.create_objects_from_elements.assert_called_with(resp.get_all_object_elms.return_value)

    def test_get_mapped_related_object(self):
        class RelatedMappingImpl(RelatedMapping):
            entity_type = 'REL'
            mapping = {}
            override_related_filters = {'override': 'this one is overridden'}

        resp = StufMappedResponseImpl('msg')
        resp.get_mapped_object = MagicMock()
        resp._get_filter_kwargs = MagicMock(return_value={'some': 'val', 'override': 'this one'})

        res = resp._get_mapped_related_object(RelatedMappingImpl(), 'some wrapper object')
        self.assertEqual(resp.get_mapped_object().get_filtered_object.return_value, res)
        resp.get_mapped_object().get_filtered_object.assert_called_with(
            some='val',
            override='this one is overridden'
        )

        resp.stuf_message.find_elm.return_value = None
        self.assertIsNone(resp._get_mapped_related_object(RelatedMappingImpl(), 'some wrapper object'))

        # Correct element is mapped
        resp.stuf_message.find_elm.assert_called_with('BG:gerelateerde', 'some wrapper object')

    def test_get_mapped_object_related(self):
        class RelatedMappingImpl(RelatedMapping):
            entity_type = 'REL'
            mapping = {'extra attr': 'attrB'}

        resp = StufMappedResponseImpl('msg')
        resp._get_mapped_related_object = MagicMock(return_value={'relatedA': 'attrA'})
        resp.stuf_message.get_elm_value = lambda x, _: {
            'attrB': 'valueB',
            'relatedA': 'valueA',
        }[x]

        res = resp.get_mapped_object('Object', RelatedMappingImpl())

        self.assertEqual({'relatedA': 'attrA', 'extra attr': 'valueB'}, res.mapped_object)

        resp._get_mapped_related_object.return_value = None
        self.assertIsNone(resp.get_mapped_object('Object', RelatedMappingImpl()))

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


import xml.etree.ElementTree as ET


class TestMappedObject(TestCase):

    def test_mapped_object(self):
        class MappedResponse(StufMappedResponse):
            @property
            def answer_section(self):
                pass
            @property
            def object_elm(self):
                pass

        xml_msg = '''
<root>
  <elm1 attr="attr">value</elm1>
  <elm2>
    <elm2sub><value>subvalue1</value></elm2sub>
    <elm2sub><value>subvalue2</value></elm2sub>
  </elm2>
  <elm3>
    <elm3sub>sub3</elm3sub>
  </elm3>
  <elm4 attr="4" />
  <elm8>
    <elm8sub x="11">1</elm8sub> 
    <elm8sub x="12">2</elm8sub> 
    <elm8sub x="13">3</elm8sub> 
  </elm8>
</root>
'''
        mapping = {
            'plain_element_value': 'elm1',
            'list_value': ['elm2 elm2sub', 'value'],
            'dict_value': {
                'a': 'elm1',
                'b': 'elm3 elm3sub'
            },
            'tuple_value': (len, 'elm1'),
            'literal_value': '=aap',
            'attribute_value': 'elm4@attr',
            'xpath_value': 'root elm8!.//elm8sub[@x="12"]'
        }
        expect = {
            'plain_element_value': 'value',
            'list_value': ['subvalue1', 'subvalue2'],
            'dict_value': {
                'a': 'value',
                'b': 'sub3'
            },
            'tuple_value': len('value'),
            'literal_value': 'aap',
            'attribute_value': '4',
            'xpath_value': '2'
        }

        response = MappedResponse(xml_msg)
        tree = ET.fromstring(xml_msg)
        result = response.get_mapped_object(tree, mapping)
        self.assertEqual(result, expect)


class TestRelatedDetailResponse(TestCase):

    resp = RelatedDetailResponse('relation')

    def test_init(self):
        self.assertEqual(self.resp.related_type, 'relation')

    @patch("gobstuf.stuf.brp.base_response.request")
    def test_filter_response(self, mock_request):
        mock_mapped_response = MagicMock()
        mock_mapped_response.relation_id = 1
        mapped_object = {
            'other': 'value',
            '_embedded': {
                'relation': [
                    {'a': 1},
                    {'a': 2}
                ],
                'other relation': []
            }
        }
        
        expected = {
            'a': 1,
            '_links': {'self': {'href': mock_request.base_url}}
        }

        result = self.resp.filter_response(mock_mapped_response, mapped_object)
        self.assertEqual(result, expected)

    @patch("gobstuf.stuf.brp.base_response.request")
    def test_filter_response_no_relations(self, mock_request):
        mock_mapped_response = MagicMock()
        mock_mapped_response.relation_id = 1
        mapped_object = {
            'other': 'value',
            '_embedded': {
                'other': [
                    {'a': 1},
                    {'a': 2}
                ]
            }
        }

    @patch("gobstuf.stuf.brp.base_response.request")
    def test_filter_response_no_relation(self, mock_request):
        mock_mapped_response = MagicMock()
        mock_mapped_response.relation_id = 3
        mapped_object = {
            'other': 'value',
            '_embedded': {
                'relation': [
                    {'a': 1},
                    {'a': 2}
                ]
            }
        }

        result = self.resp.filter_response(mock_mapped_response, mapped_object)
        self.assertEqual(result, None)


class TestRelatedListResponse(TestCase):

    resp = RelatedListResponse('relation')

    def test_init(self):
        self.assertEqual(self.resp.related_type, 'relation')

    @patch("gobstuf.stuf.brp.base_response.request")
    def test_filter_response(self, mock_request):
        mock_mapped_response = MagicMock()
        mapped_object = {
            'other': 'value',
            '_embedded': {
                'relation': [
                    {'a': 1},
                    {'a': 2}
                ],
                'other relation': []
            }
        }
        
        expected = {
            '_embedded': {
                'relation': [
                    {'a': 1},
                    {'a': 2}
                ]
            },
            '_links': {'self': {'href': mock_request.base_url}}
        }

        result = self.resp.filter_response(mock_mapped_response, mapped_object)
        self.assertEqual(result, expected)

    @patch("gobstuf.stuf.brp.base_response.request")
    def test_filter_response_no_relations(self, mock_request):
        mock_mapped_response = MagicMock()
        mock_mapped_response.relation_id = 1
        mapped_object = {
            'other': 'value',
            '_embedded': {
                'other': [
                    {'a': 1},
                    {'a': 2}
                ]
            }
        }
        
        expected = {
            '_embedded': {
                'relation': []
            },
            '_links': {'self': {'href': mock_request.base_url}}
        }

        result = self.resp.filter_response(mock_mapped_response, mapped_object)
        self.assertEqual(result, expected)
