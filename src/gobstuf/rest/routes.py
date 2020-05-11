from gobstuf.rest.brp.views import IngeschrevenpersonenBsnView, IngeschrevenpersonenFilterView

REST_ROUTES = [
    ('/brp/ingeschrevenpersonen', IngeschrevenpersonenFilterView.as_view('brp_ingeschrevenpersonen_list')),
    ('/brp/ingeschrevenpersonen/<bsn>', IngeschrevenpersonenBsnView.as_view('brp_ingeschrevenpersonen_bsn')),
]
