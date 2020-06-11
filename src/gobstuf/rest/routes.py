from gobstuf.rest.brp.views import (
    IngeschrevenpersonenBsnView,
    IngeschrevenpersonenBsnPartnerDetailView,
    IngeschrevenpersonenBsnPartnerListView,
    IngeschrevenpersonenFilterView
)

REST_ROUTES = [
    ('/brp/ingeschrevenpersonen', IngeschrevenpersonenFilterView.as_view('brp_ingeschrevenpersonen_list')),
    ('/brp/ingeschrevenpersonen/<bsn>', IngeschrevenpersonenBsnView.as_view('brp_ingeschrevenpersonen_bsn')),
    ('/brp/ingeschrevenpersonen/<bsn>/partners',
     IngeschrevenpersonenBsnPartnerListView.as_view('brp_ingeschrevenpersonen_bsn_partners_list')),
    ('/brp/ingeschrevenpersonen/<bsn>/partners/<partners_id>',
     IngeschrevenpersonenBsnPartnerDetailView.as_view('brp_ingeschrevenpersonen_bsn_partners_detail')),
]
