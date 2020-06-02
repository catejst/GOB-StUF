from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.rest.brp.views import (
    IngeschrevenpersonenView,
    IngeschrevenpersonenBsnView,
    IngeschrevenpersonenFilterView,
    IngeschrevenpersonenStufResponse,
    IngeschrevenpersonenBsnStufRequest
)


class TestIngeschrevenpersonenView(TestCase):
    def test_functional_query_parameters(self):
        view = IngeschrevenpersonenView()

        self.assertIn('inclusiefoverledenpersonen', view.functional_query_parameters)
        self.assertFalse(view.functional_query_parameters['inclusiefoverledenpersonen'])


class TestIngeschrevenpersonenFilterView(TestCase):
    def test_template_properties(self):
        view = IngeschrevenpersonenFilterView()


class TestIngeschrevenpersonenBsnView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufResponse, IngeschrevenpersonenBsnView.response_template)
        self.assertEqual(IngeschrevenpersonenBsnStufRequest, IngeschrevenpersonenBsnView.request_template)

    def test_get_not_found_message(self):
        kwargs = {'bsn': 'BEE ES EN'}
        self.assertEqual('Ingeschreven persoon niet gevonden met burgerservicenummer BEE ES EN.',
                         IngeschrevenpersonenBsnView().get_not_found_message(**kwargs))

    def test_functional_query_parameters(self):
        view = IngeschrevenpersonenBsnView()

        self.assertIn('inclusiefoverledenpersonen', view.functional_query_parameters)
        self.assertTrue(view.functional_query_parameters['inclusiefoverledenpersonen'])

