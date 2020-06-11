from gobstuf.stuf.brp.base_response import RelatedDetailResponse, RelatedListResponse, StufMappedResponse


class IngeschrevenpersonenStufResponse(StufMappedResponse):
    answer_section = 'soapenv:Envelope soapenv:Body BG:npsLa01 BG:antwoord'
    object_elm = 'BG:object'

    # These properties are passed to the filter method of the mapped object
    filter_kwargs = ['inclusiefoverledenpersonen']


class IngeschrevenpersonenStufPartnersDetailResponse(IngeschrevenpersonenStufResponse):
    response_type = RelatedDetailResponse('partners')


class IngeschrevenpersonenStufPartnersListResponse(IngeschrevenpersonenStufResponse):
    response_type = RelatedListResponse('partners')
