from gobstuf.rest.brp.base_view import StufRestView, StufRestFilterView
from gobstuf.stuf.brp.request.ingeschrevenpersonen import (
    IngeschrevenpersonenBsnStufRequest,
    IngeschrevenpersonenFilterStufRequest
)
from gobstuf.stuf.brp.response.ingeschrevenpersonen import IngeschrevenpersonenStufResponse


class IngeschrevenpersonenView(StufRestView):
    """
    Contains options that are applicable to all Ingeschrevenpersonen Views
    Use as first parent class
    """
    expand_options = [
        'partners'
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
        ['geboorte__datum', 'naam__geslachtsnaam'],
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
