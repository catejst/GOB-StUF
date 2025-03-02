from gobstuf.rest.brp.base_view import StufRestView, StufRestFilterView
from gobstuf.stuf.brp.request.ingeschrevenpersonen import (
    IngeschrevenpersonenBsnStufRequest,
    IngeschrevenpersonenBsnPartnerStufRequest,
    IngeschrevenpersonenBsnOudersStufRequest,
    IngeschrevenpersonenFilterStufRequest,
    IngeschrevenpersonenBsnKinderenStufRequest
)
from gobstuf.stuf.brp.response.ingeschrevenpersonen import (
    IngeschrevenpersonenStufResponse,
    IngeschrevenpersonenStufPartnersDetailResponse,
    IngeschrevenpersonenStufPartnersListResponse,
    IngeschrevenpersonenStufOudersDetailResponse,
    IngeschrevenpersonenStufOudersListResponse,
    IngeschrevenpersonenStufKinderenListResponse,
    IngeschrevenpersonenStufKinderenDetailResponse
)


class IngeschrevenpersonenView(StufRestView):
    """
    Contains options that are applicable to all Ingeschrevenpersonen Views
    Use as first parent class
    """
    expand_options = [
        'partners',
        'ouders',
        'kinderen',
    ]

    @property
    def functional_query_parameters(self):
        return {
            **super().functional_query_parameters,
            'inclusiefoverledenpersonen': False,
        }


class IngeschrevenpersonenFilterView(IngeschrevenpersonenView, StufRestFilterView):
    request_template = IngeschrevenpersonenFilterStufRequest
    response_template = IngeschrevenpersonenStufResponse

    name = 'ingeschrevenpersonen'

    query_parameter_combinations = [
        ['burgerservicenummer'],
        ['verblijfplaats__postcode', 'verblijfplaats__huisnummer'],
        ['verblijfplaats__gemeentevaninschrijving',
         'verblijfplaats__naamopenbareruimte',
         'verblijfplaats__huisnummer'],
        ['geboorte__datum', 'naam__geslachtsnaam'],
    ]

    # One or more can be used in combination with the combinations above
    optional_query_parameters = [
        'naam__voornamen',
        'naam__voorvoegsel',
        'verblijfplaats__huisletter',
        'verblijfplaats__huisnummertoevoeging',
    ]


class IngeschrevenpersonenBsnView(IngeschrevenpersonenView):
    request_template = IngeschrevenpersonenBsnStufRequest
    response_template = IngeschrevenpersonenStufResponse

    @property
    def functional_query_parameters(self):
        return {
            **super().functional_query_parameters,
            'inclusiefoverledenpersonen': True,
        }

    def get_not_found_message(self, **kwargs):
        return f"Ingeschreven persoon niet gevonden met burgerservicenummer {kwargs['bsn']}."


class IngeschrevenpersonenBsnPartnerListView(IngeschrevenpersonenBsnView):
    response_template = IngeschrevenpersonenStufPartnersListResponse


class IngeschrevenpersonenBsnPartnerDetailView(IngeschrevenpersonenBsnView):
    request_template = IngeschrevenpersonenBsnPartnerStufRequest
    response_template = IngeschrevenpersonenStufPartnersDetailResponse

    def get_not_found_message(self, **kwargs):
        return f"Ingeschreven partner voor persoon niet gevonden met burgerservicenummer {kwargs['bsn']}."


class IngeschrevenpersonenBsnOudersListView(IngeschrevenpersonenBsnView):
    response_template = IngeschrevenpersonenStufOudersListResponse


class IngeschrevenpersonenBsnOudersDetailView(IngeschrevenpersonenBsnView):
    request_template = IngeschrevenpersonenBsnOudersStufRequest
    response_template = IngeschrevenpersonenStufOudersDetailResponse

    def get_not_found_message(self, **kwargs):
        return f"Ingeschreven ouder voor persoon niet gevonden met burgerservicenummer {kwargs['bsn']}."


class IngeschrevenpersonenBsnKinderenListView(IngeschrevenpersonenBsnView):
    response_template = IngeschrevenpersonenStufKinderenListResponse


class IngeschrevenpersonenBsnKinderenDetailView(IngeschrevenpersonenBsnView):
    request_template = IngeschrevenpersonenBsnKinderenStufRequest
    response_template = IngeschrevenpersonenStufKinderenDetailResponse

    def get_not_found_message(self, **kwargs):
        return f"Ingeschreven kind voor persoon niet gevonden met burgerservicenummer {kwargs['bsn']}."
