from gobstuf.stuf.brp.base_request import StufRequest


class IngeschrevenpersonenStufRequest(StufRequest):
    template = 'ingeschrevenpersonen.xml'
    content_root_elm = 'soapenv:Body BG:npsLv01'
    soap_action = 'http://www.egem.nl/StUF/sector/bg/0310/npsLv01Integraal'

    replace_paths = {
        'bsn': 'BG:gelijk BG:inp.bsn'
    }
