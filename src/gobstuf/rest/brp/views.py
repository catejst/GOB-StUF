from gobstuf.rest.brp.base_view import StufRestView, StufRestFilterView
from gobstuf.stuf.brp.request.ingeschrevenpersonen import (
    IngeschrevenpersonenBsnStufRequest,
    IngeschrevenpersonenFilterStufRequest
)
from gobstuf.stuf.brp.response.ingeschrevenpersonen import IngeschrevenpersonenStufResponse


class IngeschrevenpersonenFilterView(StufRestFilterView):
    request_template = IngeschrevenpersonenFilterStufRequest
    response_template = IngeschrevenpersonenStufResponse
    name = 'ingeschrevenpersonen'

    query_parameter_combinations = [
        ('verblijfplaats__postcode', 'verblijfplaats__huisnummer'),
    ]


class IngeschrevenpersonenBsnView(StufRestView):
    request_template = IngeschrevenpersonenBsnStufRequest
    response_template = IngeschrevenpersonenStufResponse

    def get_not_found_message(self, **kwargs):
        return f"Ingeschreven persoon niet gevonden met burgerservicenummer {kwargs['bsn']}."
