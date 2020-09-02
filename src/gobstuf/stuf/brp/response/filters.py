from gobstuf.stuf.brp.base_response import RelatedDetailResponseFilter, RelatedListResponseFilter


class PartnersDetailResponseFilter(RelatedDetailResponseFilter):
    related_type = 'partners'


class PartnersListResponseFilter(RelatedListResponseFilter):
    related_type = 'partners'


class OudersDetailResponseFilter(RelatedDetailResponseFilter):
    related_type = 'ouders'


class OudersListResponseFilter(RelatedListResponseFilter):
    related_type = 'ouders'
