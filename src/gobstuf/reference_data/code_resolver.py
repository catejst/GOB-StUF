import os
import csv


class DataNotFoundException(Exception):
    pass


class DataItemNotFoundException(Exception):
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
    _gemeenten_omschrijving = {}

    @classmethod
    def initialize(cls):
        """
        Load landen table at startup

        :return:
        """
        cls._gemeenten = cls._load_data(cls.GEMEENTEN, cls.CODE)
        cls._gemeenten_omschrijving = cls._load_data(cls.GEMEENTEN, cls.DESCRIPTION)
        cls._landen = cls._load_data(cls.LANDEN, cls.CODE)

    @classmethod
    def _load_data(cls, config, key_field):
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
            raise DataNotFoundException(f"ERROR: Table {config['table']} not found")

        data = {}
        for line in lines[1:]:  # Skip header
            code = line[config['fields'][key_field]]
            data[code] = {
                attr: line[index] for attr, index in config['fields'].items()
            }
        return data

    @classmethod
    def _get_dataitem(cls, data, key, value_field):
        """
        Get the value field for the given code

        :param data: The dictionary to search in
        :param key: The key to look for
        :param value_field: Which field to return from the dictionary
        :return:
        """
        assert data, f"{cls.__name__} initialize method not called"

        if not key:
            return

        try:
            return data[key][value_field]
        except KeyError:
            raise DataItemNotFoundException(f"ERROR: {key} could not be found")

    @classmethod
    def format_code(cls, code):
        """
        Pad a code to 4 digits if it contains a value

        :param code:
        :return:
        """
        return code.zfill(4) if code else code

    @classmethod
    def get_land(cls, code):
        """
        Get the land name for the given code, padded to 4 digits

        :param code:
        :return:
        """
        return cls._get_dataitem(cls._landen, cls.format_code(code), cls.DESCRIPTION)

    @classmethod
    def get_gemeente(cls, code):
        """
        Get the gemeente naam for the given code, padded to 4 digits

        :param code:
        :return:
        """
        return cls._get_dataitem(cls._gemeenten, cls.format_code(code), cls.DESCRIPTION)

    @classmethod
    def get_gemeente_code(cls, omschrijving):
        """
        Get the gemeente code for the given omschrijving

        :param naam:
        :return:
        """
        return cls._get_dataitem(cls._gemeenten_omschrijving, omschrijving, cls.CODE)


CodeResolver.initialize()
