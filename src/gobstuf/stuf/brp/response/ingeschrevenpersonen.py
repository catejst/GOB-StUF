from gobstuf.stuf.brp.base_response import StufMappedResponse


class IngeschrevenpersonenStufResponse(StufMappedResponse):
    answer_section = 'soapenv:Envelope soapenv:Body BG:npsLa01 BG:antwoord'
    object_elm = 'BG:object'

    mapping = {
        'burgerservicenummer': 'BG:inp.bsn',
    }
