from gobstuf.rest.brp.base_view import StufRestView
from gobstuf.stuf.brp.request.ingeschrevenpersonen import IngeschrevenpersonenStufRequest
from gobstuf.stuf.brp.response.ingeschrevenpersonen import IngeschrevenpersonenStufResponse


class IngeschrevenpersonenView(StufRestView):
    request_template = IngeschrevenpersonenStufRequest
    response_template = IngeschrevenpersonenStufResponse

    def get_not_found_message(self, **kwargs):
        return f"Ingeschreven persoon niet gevonden met burgerservicenummer {kwargs['bsn']}."
