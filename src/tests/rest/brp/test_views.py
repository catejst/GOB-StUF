from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.rest.brp.views import (
    IngeschrevenpersonenBsnView,
    IngeschrevenpersonenFilterView,
    IngeschrevenpersonenStufResponse,
    IngeschrevenpersonenBsnStufRequest
)


class TestIngeschrevernpersonenFilterView(TestCase):
    def test_template_properties(self):
        view = IngeschrevenpersonenFilterView()
        self.assertEqual(False, view.response_template_properties['inclusiefoverledenpersonen'])


class TestIngeschrevenpersonenBsnView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufResponse, IngeschrevenpersonenBsnView.response_template)
        self.assertEqual(IngeschrevenpersonenBsnStufRequest, IngeschrevenpersonenBsnView.request_template)

    def test_get_not_found_message(self):
        kwargs = {'bsn': 'BEE ES EN'}
        self.assertEqual('Ingeschreven persoon niet gevonden met burgerservicenummer BEE ES EN.',
                         IngeschrevenpersonenBsnView().get_not_found_message(**kwargs))

