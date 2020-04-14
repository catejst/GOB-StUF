from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.rest.brp.views import (
    IngeschrevenpersonenView,
    IngeschrevenpersonenStufResponse,
    IngeschrevenpersonenStufRequest
)


class TestIngeschrevenpersonenView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufResponse, IngeschrevenpersonenView.response_template)
        self.assertEqual(IngeschrevenpersonenStufRequest, IngeschrevenpersonenView.request_template)

    def test_get_not_found_message(self):
        kwargs = {'bsn': 'BEE ES EN'}
        self.assertEqual('Ingeschreven persoon niet gevonden met burgerservicenummer BEE ES EN',
                         IngeschrevenpersonenView().get_not_found_message(**kwargs))

