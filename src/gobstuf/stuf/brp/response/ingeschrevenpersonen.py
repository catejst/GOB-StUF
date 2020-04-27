from gobstuf.stuf.brp.base_response import StufMappedResponse
from gobstuf.mks_utils import MKSConverter


class IngeschrevenpersonenStufResponse(StufMappedResponse):
    answer_section = 'soapenv:Envelope soapenv:Body BG:npsLa01 BG:antwoord'
    object_elm = 'BG:object'

    # Response parameters, Fixed class variable for now
    inclusiefoverledenpersonen = False

    mapping = {
        'geslachtsaanduiding': (MKSConverter.as_geslachtsaanduiding, 'BG:geslachtsaanduiding'),
        'naam': {
            'aanduidingNaamgebruik': (MKSConverter.as_aanduiding_naamgebruik, 'BG:aanduidingNaamgebruik'),
            'voornamen': 'BG:voornamen',
            'voorletters': 'BG:voorletters',
            'geslachtsnaam': 'BG:geslachtsnaam',
            'voorvoegsel': 'BG:voorvoegselGeslachtsnaam',
        },
        'leeftijd': (MKSConverter.as_leeftijd, 'BG:geboortedatum'),
        'burgerservicenummer': 'BG:inp.bsn',
        'geboorte': {
            'datum': (MKSConverter.as_datum_broken_down, 'BG:geboortedatum'),
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

    def get_links(self):
        """
        Return the HAL links that correspond with the mapped object

        :param mapped_object:
        :return:
        """
        mapped_object = self.get_mapped_object()
        links = {}
        try:
            nummeraanduiding = mapped_object['verblijfplaats']['identificatiecodeNummeraanduiding']
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
