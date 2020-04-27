from gobstuf.stuf.brp.base_response import StufMappedResponse
from gobstuf.mks_utils import MKSConverter


class IngeschrevenpersonenStufResponse(StufMappedResponse):
    answer_section = 'soapenv:Envelope soapenv:Body BG:npsLa01 BG:antwoord'
    object_elm = 'BG:object'

    # Response parameters, Fixed class variable for now
    inclusiefoverledenpersonen = True

    mapping = {
        'geslachtsaanduiding': (MKSConverter.as_geslachtsaanduiding, 'BG:geslachtsaanduiding'),
        'naam': {
            'aanduidingNaamgebruik': (MKSConverter.as_aanduiding_naamgebruik, 'BG:aanduidingNaamgebruik'),
            'voornamen': 'BG:voornamen',
            'voorletters': 'BG:voorletters',
            'geslachtsnaam': 'BG:geslachtsnaam',
            'voorvoegsel': 'BG:voorvoegselGeslachtsnaam',
        },
        'leeftijd': (MKSConverter.as_leeftijd, 'BG:geboortedatum',
                                               'BG:geboortedatum@StUF:indOnvolledigeDatum',
                                               'BG:overlijdensdatum'),
        'burgerservicenummer': 'BG:inp.bsn',
        'geboorte': {
            'datum':
                (MKSConverter.as_datum_broken_down, 'BG:geboortedatum',
                                                    'BG:geboortedatum@StUF:indOnvolledigeDatum'),
        },
        'verblijfplaats': {
            'functieAdres': '=woonadres',
            'identificatiecodeNummeraanduiding': 'BG:verblijfsadres BG:aoa.identificatie',
            'huisletter': 'BG:verblijfsadres BG:aoa.huisletter',
            'huisnummer': 'BG:verblijfsadres BG:aoa.huisnummer',
            'huisnummertoevoeging': 'BG:verblijfsadres BG:aoa.huisnummertoevoeging',
            'postcode': 'BG:verblijfsadres BG:aoa.postcode',
            'woonplaatsnaam': 'BG:verblijfsadres BG:wpl.woonplaatsNaam',
            'straatnaam': 'BG:verblijfsadres BG:gor.straatnaam',
            'datumAanvangAdreshouding': (MKSConverter.as_datum_broken_down, 'BG:verblijfsadres BG:begindatumVerblijf'),
            'datumInschrijvingInGemeente': (MKSConverter.as_datum_broken_down, 'BG:inp.datumInschrijving'),
            'gemeenteVanInschrijving': {
                'code': (MKSConverter.as_code(4), 'BG:inp.gemeenteVanInschrijving'),
                'omschrijving': (MKSConverter.get_gemeente_omschrijving, 'BG:inp.gemeenteVanInschrijving')
            },
        },
        'overlijdensdatum': 'BG:overlijdensdatum'
    }

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

    def get_filtered_object(self, mapped_object):
        """
        Filter the mapped object on overlijdensdatum

        Default is to not return overleden personen
        :param mapped_object: The mapped response object
        :return:
        """
        is_overleden = mapped_object.get('overlijdensdatum') is not None
        if is_overleden and not self.inclusiefoverledenpersonen:
            # Skip overleden personen, unless explicitly included
            mapped_object = None
        return super().get_filtered_object(mapped_object)
