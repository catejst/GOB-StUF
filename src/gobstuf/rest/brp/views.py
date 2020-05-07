from gobstuf.rest.brp.base_view import StufRestView
from gobstuf.stuf.brp.request.ingeschrevenpersonen import IngeschrevenpersonenBsnStufRequest
from gobstuf.stuf.brp.response.ingeschrevenpersonen import IngeschrevenpersonenStufResponse


class IngeschrevenpersonenBsnView(StufRestView):
    request_template = IngeschrevenpersonenBsnStufRequest
    response_template = IngeschrevenpersonenStufResponse

    def get_not_found_message(self, **kwargs):
        return f"Ingeschreven persoon niet gevonden met burgerservicenummer {kwargs['bsn']}."
