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
            'datumInschrijvingInGemeente': (MKSConverter.as_datum_broken_down, 'BG:inp.datumInschrijving'),
            'gemeenteVanInschrijving': {
                'code': (MKSConverter.as_code(4), 'BG:inp.gemeenteVanInschrijving'),
                'omschrijving': (MKSConverter.get_gemeente_omschrijving, 'BG:inp.gemeenteVanInschrijving')
            },
            'woonadres': {
                'identificatiecodeNummeraanduiding':
                    'BG:inp.verblijftIn BG:gerelateerde StUF:extraElementen' +
                    '!.//StUF:extraElement[@naam="identificatieNummerAanduiding"]',
                'identificatiecodeAdresseerbaarObject': 'BG:verblijfsadres BG:aoa.identificatie',
                'huisletter': 'BG:verblijfsadres BG:aoa.huisletter',
                'huisnummer': 'BG:verblijfsadres BG:aoa.huisnummer',
                'huisnummertoevoeging': 'BG:verblijfsadres BG:aoa.huisnummertoevoeging',
                'postcode': 'BG:verblijfsadres BG:aoa.postcode',
                'woonplaatsnaam': 'BG:verblijfsadres BG:wpl.woonplaatsNaam',
                'straatnaam': 'BG:verblijfsadres BG:gor.straatnaam',
                'datumAanvangAdreshouding':
                    (MKSConverter.as_datum_broken_down, 'BG:verblijfsadres BG:begindatumVerblijf'),
            },
            'briefadres': {
                'identificatiecodeAdresseerbaarObject': 'BG:sub.correspondentieAdres BG:aoa.identificatie',
                'huisletter': 'BG:sub.correspondentieAdres BG:aoa.huisletter',
                'huisnummer': 'BG:sub.correspondentieAdres BG:aoa.huisnummer',
                'huisnummertoevoeging': 'BG:sub.correspondentieAdres BG:aoa.huisnummertoevoeging',
                'postcode': 'BG:sub.correspondentieAdres BG:postcode',
                'woonplaatsnaam': 'BG:sub.correspondentieAdres BG:wpl.woonplaatsNaam',
                'straatnaam': 'BG:sub.correspondentieAdres BG:gor.straatnaam'
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

        Filter the mapped object on either woonadres or briefadres

        :param mapped_object: The mapped response object
        :return:
        """
        # Set verblijfplaats: default use woonadres, fallback is briefadres
        verblijfplaats = mapped_object['verblijfplaats']
        for functie_adres in ['woonadres', 'briefadres']:
            adres = verblijfplaats[functie_adres]
            del verblijfplaats[functie_adres]
            if not verblijfplaats.get('functieAdres') and any(adres.values()):
                # Take the first adrestype that has any values
                verblijfplaats = {
                    'functieAdres': functie_adres,
                    **adres,
                    **verblijfplaats
                }
        mapped_object['verblijfplaats'] = verblijfplaats

        # Use overlijdensdatum for filtering
        is_overleden = mapped_object.get('overlijdensdatum') is not None
        if is_overleden and not self.inclusiefoverledenpersonen:
            # Skip overleden personen, unless explicitly included
            mapped_object = None
        return super().get_filtered_object(mapped_object)
