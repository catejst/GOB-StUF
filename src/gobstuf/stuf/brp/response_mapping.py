from typing import Type
from abc import ABC, abstractmethod
from flask import url_for, request

from gobstuf.mks_utils import MKSConverter


def flask_url(view_name, **kwargs):
    url = url_for(view_name, **kwargs)
    return f"{request.scheme}://{request.host}{url}"


class Mapping(ABC):
    """Defines a mapping between a dict (used for REST responses) and a StUF message.

    Provides a filter method to filter out attributes and/or objects
    """

    @property
    def related(self) -> dict:
        return {}

    @property
    @abstractmethod
    def mapping(self) -> dict:  # pragma: no cover
        pass

    @property
    @abstractmethod
    def entity_type(self) -> str:  # pragma: no cover
        pass

    def get_links(self, mapped_object) -> dict:
        return {}

    def filter(self, mapped_object: dict, **kwargs):
        """
        Filter the mapped object on the mapped attribute values
        Default implementation is to filter out any null values

        Any derived class that implements this method should call this super method on its result
        super().filter(result)

        :param mapped_object:
        :return:
        """

        def filter_none_values(obj):
            """
            Recursively filter out any None values of the given object

            :param obj:
            :return:
            """
            result = {}
            for k, v in obj.items():
                if isinstance(v, dict):
                    value = filter_none_values(v)
                    if value:
                        result[k] = value
                elif v is not None:
                    result[k] = v
            return result

        return filter_none_values(mapped_object) if mapped_object else mapped_object


class StufObjectMapping:
    """Class holding all Mapping objects. Call register() with each Mapping to make the mapping available.

    """
    mappings = {}

    @classmethod
    def get_for_entity_type(cls, entity_type: str):
        mapping = cls.mappings.get(entity_type)

        if not mapping:
            raise Exception(f"Can't find mapping for entity type {entity_type}")
        return mapping()

    @classmethod
    def register(cls, mapping: Type[Mapping]):
        cls.mappings[mapping().entity_type] = mapping


class NPSMapping(Mapping):
    """NPS mapping, for Natuurlijke Personen

    """

    @property
    def entity_type(self):
        return 'NPS'

    @property
    def mapping(self):

        communicatie_parameters = {
            'persoon': {
                'geslachtsaanduiding': (MKSConverter.as_geslachtsaanduiding, 'BG:geslachtsaanduiding'),
                'naam': {
                    'aanduidingNaamgebruik': (MKSConverter.as_aanduiding_naamgebruik, 'BG:aanduidingNaamgebruik'),
                    'voorletters': 'BG:voorletters',
                    'geslachtsnaam': 'BG:geslachtsnaam',
                    'voorvoegsel': 'BG:voorvoegselGeslachtsnaam',
                }
            },
            'partners': ['BG:inp.heeftAlsEchtgenootPartner', {
                'naam': {
                    'geslachtsnaam': 'BG:gerelateerde BG:geslachtsnaam',
                    'voorvoegsel': 'BG:gerelateerde BG:voorvoegselGeslachtsnaam',
                },
                'aangaanHuwelijkPartnerschap': {
                    'datum': 'BG:datumSluiting'
                },
                'ontbindingHuwelijkPartnerschap': {
                    'datum': 'BG:datumOntbinding'
                }
            }]
        }

        return {
            'geslachtsaanduiding': (MKSConverter.as_geslachtsaanduiding, 'BG:geslachtsaanduiding'),
            'naam': {
                'aanhef': (MKSConverter.get_aanhef, communicatie_parameters),
                'aanschrijfwijze': (MKSConverter.get_aanschrijfwijze, communicatie_parameters),
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
            'overlijden': {
                'indicatieOverleden': (MKSConverter.true_if_exists, 'BG:overlijdensdatum'),
                'datum': (MKSConverter.as_datum_broken_down, 'BG:overlijdensdatum'),
                'land': {
                    'code': (MKSConverter.as_code(4), 'BG:inp.overlijdenLand'),
                    'omschrijving': (MKSConverter.get_land_omschrijving, 'BG:inp.overlijdenLand')
                },
                'plaats': {
                    'code': (MKSConverter.as_code(4), 'BG:inp.overlijdenplaats'),
                    'omschrijving': (MKSConverter.get_gemeente_omschrijving, 'BG:inp.overlijdenplaats')
                }
            }
        }

    @property
    def related(self):  # pragma: no cover
        return {
            'partners': 'BG:inp.heeftAlsEchtgenootPartner',
        }

    def filter(self, mapped_object: dict, **kwargs):
        """
        Filter the mapped object on overlijdensdatum
        Overleden personen are returned based on the inclusiefoverledenpersonen kwarg

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
        is_overleden = mapped_object['overlijden']['indicatieOverleden']
        if is_overleden and not kwargs.get('inclusiefoverledenpersonen', False):
            # Skip overleden personen, unless explicitly included
            mapped_object = None
        return super().filter(mapped_object)

    def get_links(self, mapped_object: dict):
        """
        Return the HAL links that correspond with the mapped and filtered object (data)

        :param data: the mapped and filtered object
        :return:
        """
        links = super().get_links(mapped_object)

        try:
            nummeraanduiding = mapped_object['verblijfplaats']['woonadres']['identificatiecodeNummeraanduiding']
        except KeyError:
            pass
        else:
            links['verblijfplaatsNummeraanduiding'] = {
                'href': f"https://api.data.amsterdam.nl/gob/bag/nummeraanduidingen/{nummeraanduiding}/"
            }

        if mapped_object.get('burgerservicenummer'):
            links['self'] = {
                'href': flask_url('brp_ingeschrevenpersonen_bsn', bsn=mapped_object['burgerservicenummer'])
            }

        return links


StufObjectMapping.register(NPSMapping)


class RelatedMapping(Mapping):
    """RelatedMapping is the mapping of a StUF element holding a related element.

    For example:

    <BG:inp.heeftAlsEchtgenootPartner StUF:entiteittype="NPSNPSHUW">
        <BG:gerelateerde StUF:entiteittype="NPS">
        ...
        </BG:gerelateerde>
        <other attrs />
    </BG:inp.heeftAlsEchtgenootPartner>

    The RelatedMapping has the element with type NPSNPSHUW as root. The embedded element with type NPS is the related
    object. All attributes that are defined in the NPSMapping are included in this mapping, based on the
    include_related property of this class.
    On top of these inherited attributes, a RelatedMapping can define its own mapping.

    The result is a combination of attributes from the embedded type (NPS) and the attributes defined on the
    NPSNPSHUW class.
    """

    @property
    def related_entity_wrapper(self):  # pragma: no cover
        return 'BG:gerelateerde'

    @property
    def include_related(self):  # pragma: no cover
        return []

    @property
    def override_related_filters(self):  # pragma: no cover
        return {}

    def filter(self, mapped_object: dict, **kwargs):
        """Filters :mapped_object:. Only keeps the keys present in self.mapping and self.include_related.

        The mapped_object includes ALL keys from the related mapping, plus the keys we defined in this instance.
        However, we only need the keys from the related mapping defined in include_related, plus our own mapped
        attributes.

        This method filters out all keys from the related entity we don't need.

        :param mapped_object:
        :param kwargs:
        :return:
        """
        mapped_object = {k: v for k, v in mapped_object.items() if k in
                         self.include_related + list(self.mapping.keys())
                         }

        return super().filter(mapped_object)


class NPSNPSHUWMapping(RelatedMapping):

    @property
    def entity_type(self):  # pragma: no cover
        return 'NPSNPSHUW'

    @property
    def override_related_filters(self):  # pragma: no cover
        return {
            'inclusiefoverledenpersonen': True,
        }

    # Include these attributes from the embedded (NPS) object
    @property
    def include_related(self):  # pragma: no cover
        return [
            'burgerservicenummer',
            'geboorte',
            'naam'
        ]

    # And add these attributes
    @property
    def mapping(self):  # pragma: no cover
        return {
            'aangaanHuwelijkPartnerschap': {
                'datum': (MKSConverter.as_datum_broken_down,
                          'BG:datumSluiting',
                          'BG:datumSluiting@StUF:indOnvolledigeDatum')
            },
            # datumOntbinding is used to filter out 'ontbonden huwelijken'.
            # Note that this field will never be exposed because its value will be None on exposed objects.
            'datumOntbinding': 'BG:datumOntbinding'
        }

    def filter(self, mapped_object: dict, **kwargs):
        """Filters out 'ontbonden huwelijken'

        :param mapped_object:
        :param kwargs:
        :return:
        """
        if mapped_object.get('datumOntbinding'):
            # Filter out 'ontbonden huwelijk'
            return None

        return super().filter(mapped_object, **kwargs)

    def get_links(self, mapped_object: dict) -> dict:
        links = super().get_links(mapped_object)

        if mapped_object.get('burgerservicenummer'):
            links['ingeschrevenPersoon'] = {
                'href': flask_url('brp_ingeschrevenpersonen_bsn', bsn=mapped_object['burgerservicenummer'])
            }
        return links


StufObjectMapping.register(NPSNPSHUWMapping)
