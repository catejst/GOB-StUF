from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.rest.brp.views import (
    IngeschrevenpersonenView,
    IngeschrevenpersonenBsnView,
    IngeschrevenpersonenBsnPartnerListView,
    IngeschrevenpersonenBsnPartnerDetailView,
    IngeschrevenpersonenFilterView,
    IngeschrevenpersonenStufResponse,
    IngeschrevenpersonenStufPartnersListResponse,
    IngeschrevenpersonenStufPartnersDetailResponse,
    IngeschrevenpersonenBsnStufRequest,
    IngeschrevenpersonenBsnPartnerStufRequest,
    IngeschrevenpersonenBsnOudersListView,
    IngeschrevenpersonenBsnOudersDetailView,
    IngeschrevenpersonenStufOudersDetailResponse,
    IngeschrevenpersonenStufOudersListResponse,
    IngeschrevenpersonenBsnOudersStufRequest,
    IngeschrevenpersonenBsnKinderenListView,
    IngeschrevenpersonenBsnKinderenDetailView,
    IngeschrevenpersonenStufKinderenDetailResponse,
    IngeschrevenpersonenStufKinderenListResponse,
    IngeschrevenpersonenBsnKinderenStufRequest,
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


class TestIngeschrevenpersonenBsnPartnerListView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufPartnersListResponse, IngeschrevenpersonenBsnPartnerListView.response_template)
        self.assertEqual(IngeschrevenpersonenBsnStufRequest, IngeschrevenpersonenBsnPartnerListView.request_template)


class TestIngeschrevenpersonenBsnPartnerDetailView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufPartnersDetailResponse, IngeschrevenpersonenBsnPartnerDetailView.response_template)
        self.assertEqual(IngeschrevenpersonenBsnPartnerStufRequest, IngeschrevenpersonenBsnPartnerDetailView.request_template)

    def test_get_not_found_message(self):
        kwargs = {'bsn': 'BEE ES EN'}
        self.assertEqual('Ingeschreven partner voor persoon niet gevonden met burgerservicenummer BEE ES EN.',
                         IngeschrevenpersonenBsnPartnerDetailView().get_not_found_message(**kwargs))


class TestIngeschrevenpersonenBsnOudersListView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufOudersListResponse, IngeschrevenpersonenBsnOudersListView.response_template)
        self.assertEqual(IngeschrevenpersonenBsnStufRequest, IngeschrevenpersonenBsnOudersListView.request_template)


class TestIngeschrevenpersonenBsnOudersDetailView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufOudersDetailResponse, IngeschrevenpersonenBsnOudersDetailView.response_template)
        self.assertEqual(IngeschrevenpersonenBsnOudersStufRequest, IngeschrevenpersonenBsnOudersDetailView.request_template)

    def test_get_not_found_message(self):
        kwargs = {'bsn': 'BEE ES EN'}
        self.assertEqual('Ingeschreven ouder voor persoon niet gevonden met burgerservicenummer BEE ES EN.',
                         IngeschrevenpersonenBsnOudersDetailView().get_not_found_message(**kwargs))


class TestIngeschrevenpersonenBsnKinderenListView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufKinderenListResponse, IngeschrevenpersonenBsnKinderenListView.response_template)
        self.assertEqual(IngeschrevenpersonenBsnStufRequest, IngeschrevenpersonenBsnKinderenListView.request_template)


class TestIngeschrevenpersonenBsnKinderenDetailView(TestCase):

    @patch("gobstuf.rest.brp.views.StufRestView", MagicMock())
    def test_templates_set(self):
        self.assertEqual(IngeschrevenpersonenStufKinderenDetailResponse, IngeschrevenpersonenBsnKinderenDetailView.response_template)
        self.assertEqual(IngeschrevenpersonenBsnKinderenStufRequest, IngeschrevenpersonenBsnKinderenDetailView.request_template)

    def test_get_not_found_message(self):
        kwargs = {'bsn': 'BEE ES EN'}
        self.assertEqual('Ingeschreven kind voor persoon niet gevonden met burgerservicenummer BEE ES EN.',
                         IngeschrevenpersonenBsnKinderenDetailView().get_not_found_message(**kwargs))
