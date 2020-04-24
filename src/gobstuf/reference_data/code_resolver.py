import requests
from requests.exceptions import HTTPError, ConnectionError
import os
import csv


class CodeNotFoundException(Exception):
    pass


class CodeResolver:

    # Landen configuratie
    LANDEN_TABEL = 'Tabel34 Landentabel (gesorteerd op code).csv'
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    LANDEN_PATH = os.path.join(DATA_DIR, LANDEN_TABEL)
    LANDEN_FIELDS = {
        'landcode': 0,
        'omschrijving': 1,
        'datum_ingang': 2,
        'datum_einde': 3,
        'fictieve_datum_einde': 4,
    }

    # Gemeenten configuratie
    GOB_URL = "https://api.data.amsterdam.nl/gob/graphql/"

    # Local dictionaries
    _landen = {}
    _gemeenten = {}

    @classmethod
    def initialize(cls):
        """
        Load landen table at startup

        :return:
        """
        cls._landen = cls._load_landen()

    @classmethod
    def _load_landen(cls):
        """
        Load landen table from internal data file

        See README for details how to refresh tha landen table
        :return:
        """
        try:
            with open(cls.LANDEN_PATH, 'r', encoding='utf16') as f:
                lines = [line for line in csv.reader(f)]
        except FileNotFoundError:
            raise CodeNotFoundException(f"ERROR: landentabel {cls.LANDEN_TABEL} could not be found")

        landen = {}
        for line in lines[1:]:  # Skip header
            landcode = line[cls.LANDEN_FIELDS['landcode']]
            landen[landcode] = {
                attr: line[index] for attr, index in cls.LANDEN_FIELDS.items()
            }
        return landen

    @classmethod
    def get_land(cls, code):
        """
        Get the land name for the given code

        :param code:
        :return:
        """
        assert cls._landen, f"{cls.__name__} initialize method not called"

        if not code:
            return

        code = code.zfill(4)
        try:
            return cls._landen[code]['omschrijving']
        except KeyError:
            print(f"ERROR: Land {code} could not be found")

    @classmethod
    def _load_gemeente(cls, code):
        # Construct a GraphQL query to retrieve the name for the given code
        entity = 'brkGemeentes'
        attr = 'naam'
        query = """
{
  %s (identificatie:"%s") {
    edges {
      node {
        %s
      }
    }
  }
}""" % (entity, code, attr)

        # Construct the URL for the GraphQL query
        url = f"{cls.GOB_URL}?query={query}"

        try:
            result = requests.get(url)
            result.raise_for_status()
            return result.json()['data'][entity]['edges'][0]['node'][attr]
        except (HTTPError, ConnectionError) as e:
            raise CodeNotFoundException(f"ERROR: Request {cls.GOB_URL} failed for query {query} ({str(e)})")
        except (KeyError, IndexError):
            raise CodeNotFoundException(f"ERROR: Gemeente {code} could not be found")

    @classmethod
    def get_gemeente(cls, code):
        """
        Get the gemeente naam for the given code

        :param code:
        :return:
        """
        if not code:
            return

        code = code.zfill(4)
        if not cls._gemeenten.get(code):
            try:
                cls._gemeenten[code] = cls._load_gemeente(code)
            except CodeNotFoundException as e:
                print(str(e))
                return
        return cls._gemeenten[code]


CodeResolver.initialize()
# for i in [1, 2]:
#     result = CodeResolver.get_land('5002')
#     print(result)
#     result = CodeResolver.get_gemeente('0363')
#     print(result)
