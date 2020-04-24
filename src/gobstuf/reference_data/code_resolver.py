import os
import csv


class CodeNotFoundException(Exception):
    pass


class CodeResolver:

    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    # Maps code on omschrijving
    CODE = 'code'
    DESCRIPTION = 'omschrijving'

    # Landen configuratie
    LANDEN = {
        'table': 'Tabel34 Landentabel (gesorteerd op code).csv',
        'fields': {
            CODE: 0,
            DESCRIPTION: 1,
            'datum_ingang': 2,
            'datum_einde': 3,
            'fictieve_datum_einde': 4,
        },
    }

    # Gemeenten configuratie
    GEMEENTEN = {
        'table': 'Tabel33 Gemeententabel (gesorteerd op code).csv',
        'fields': {
            CODE: 0,
            DESCRIPTION: 1,
            'nieuwe_code': 2,
            'datum_ingang': 3,
            'datum_einde': 4
        }
    }

    # Local dictionaries
    _landen = {}
    _gemeenten = {}

    @classmethod
    def initialize(cls):
        """
        Load landen table at startup

        :return:
        """
        cls._gemeenten = cls._load_data(cls.GEMEENTEN)
        cls._landen = cls._load_data(cls.LANDEN)

    @classmethod
    def _load_data(cls, config):
        """
        Load reference data from internal data file

        See README for details how to refresh the reference data
        :return:
        """
        path = os.path.join(cls.DATA_DIR, config['table'])
        try:
            with open(path, 'r', encoding='utf16') as f:
                lines = [line for line in csv.reader(f)]
        except FileNotFoundError:
            raise CodeNotFoundException(f"ERROR: Table {config['table']} not found")

        data = {}
        for line in lines[1:]:  # Skip header
            code = line[config['fields'][cls.CODE]]
            data[code] = {
                attr: line[index] for attr, index in config['fields'].items()
            }
        return data

    @classmethod
    def _get_dataitem(cls, data, code):
        """
        Get the description for the given code

        :param code:
        :return:
        """
        assert data, f"{cls.__name__} initialize method not called"

        if not code:
            return

        code = code.zfill(4)
        try:
            return data[code][cls.DESCRIPTION]
        except KeyError:
            print(f"ERROR: {code} could not be found")

    @classmethod
    def get_land(cls, code):
        """
        Get the land name for the given code

        :param code:
        :return:
        """
        return cls._get_dataitem(cls._landen, code)

    @classmethod
    def get_gemeente(cls, code):
        """
        Get the gemeente naam for the given code

        :param code:
        :return:
        """
        return cls._get_dataitem(cls._gemeenten, code)


CodeResolver.initialize()
