from gobstuf.stuf.brp.base_response import StufMappedResponse


class IngeschrevenpersonenStufResponse(StufMappedResponse):
    answer_section = 'soapenv:Envelope soapenv:Body BG:npsLa01 BG:antwoord'
    object_elm = 'BG:object'

    # Response parameters. Defaults to True, can be overridden with response_template_properties
    inclusiefoverledenpersonen = True

    # These properties are passed to the filter method of the mapped object
    filter_kwargs = ['inclusiefoverledenpersonen']

    def get_links(self, data):
        """
        Return the HAL links that correspond with the mapped and filtered object (data)

        :param data: the mapped and filtered object
        :return:
        """
        links = {}
        try:
            nummeraanduiding = data['verblijfplaats']['identificatiecodeNummeraanduiding']
        except KeyError:
            pass
        else:
            links['verblijfplaatsNummeraanduiding'] = {
                'href': f"https://api.data.amsterdam.nl/gob/bag/nummeraanduidingen/{nummeraanduiding}/"
            }
        return links
