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
            'aanduidingNaamgebruik': 'BG:aanduidingNaamgebruik',
            'voornamen': 'BG:voornamen',
            'voorletters': 'BG:voorletters',
            'geslachtsnaam': 'BG:geslachtsnaam',
            'voorvoegsel': 'BG:voorvoegselGeslachtsnaam',
        },
        'leeftijd': (MKSConverter.as_leeftijd, 'BG:geboortedatum'),
        'burgerservicenummer': 'BG:inp.bsn',
        'geboorte': {
            'datum': {
                'datum': (MKSConverter.as_datum, 'BG:geboortedatum'),
                'jaar': (MKSConverter.as_jaar, 'BG:geboortedatum'),
                'maand': (MKSConverter.as_maand, 'BG:geboortedatum'),
                'dag': (MKSConverter.as_dag, 'BG:geboortedatum'),
            },
        },
        'overlijdensdatum': 'BG:overlijdensdatum'
    }

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
