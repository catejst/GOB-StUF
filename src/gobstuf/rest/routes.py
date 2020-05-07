from gobstuf.rest.brp.views import IngeschrevenpersonenBsnView

REST_ROUTES = [
    ('/brp/ingeschrevenpersonen/<bsn>', IngeschrevenpersonenBsnView.as_view('brp_ingeschrevenpersonen_bsn')),
]
