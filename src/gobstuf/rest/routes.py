from gobstuf.rest.brp.views import IngeschrevenpersonenView

REST_ROUTES = [
    ('/brp/ingeschrevenpersonen/<bsn>', IngeschrevenpersonenView.as_view('brp_ingeschrevenpersonen')),
]
