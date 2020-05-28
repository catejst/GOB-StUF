import os
import pytz
import datetime
import random
import sys

from abc import ABC, abstractmethod

from gobstuf.stuf.message import StufMessage

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'request_template')


class StufRequest(ABC):
    """Creates a new StUF request, based on a template from an *.xml file.

    Replaces gebruiker and applicatie in the XML file, as well as the key/values defined in values.

    """
    default_tz = 'Europe/Amsterdam'

    # Paths within the template
    applicatie_path = 'BG:stuurgegevens StUF:zender StUF:applicatie'
    gebruiker_path = 'BG:stuurgegevens StUF:zender StUF:gebruiker'
    tijdstip_bericht_path = 'BG:stuurgegevens StUF:tijdstipBericht'
    referentienummer_path = 'BG:stuurgegevens StUF:referentienummer'

    parameter_checks = {}

    def __init__(self, gebruiker: str, applicatie: str):
        """

        :param gebruiker: MKS gebruiker
        :param applicatie: MKS applicatie
        """
        self.gebruiker = gebruiker
        self.applicatie = applicatie
        self.stuf_message = None

        self._load()

        self._set_applicatie(applicatie)
        self._set_gebruiker(gebruiker)

    def _set_applicatie(self, applicatie: str):
        self.set_element(self.applicatie_path, applicatie)

    def _set_gebruiker(self, gebruiker: str):
        self.set_element(self.gebruiker_path, gebruiker)

    def set_values(self, values: dict):
        """Sets values in XML. Accepts a dict with {key: value} pairs, where key exists in
        replace_paths and value is the new value of the matching path.

        :param values:
        :return:
        """
        assert set(values.keys()) <= set(self.parameter_paths.keys())

        for key, value in values.items():
            self.set_element(self.parameter_paths[key], self._convert_parameter_value(key, value))

    def _convert_parameter_value(self, key: str, value: str):
        """Converts parameter value for key before injecting the value in the template.
        Looks for a method convert_param_{KEY} to convert value. If such a method doesn't exist, value is returned
        without conversion.

        Used, for example for geboorte__datum. The incoming value is of the format YYYY-MM-DD, but this value needs to
        be converted to the format YYYYMMDD

        :param key:
        :param value:
        :return:
        """
        convert_func = getattr(self, f'convert_param_{key}', None)

        if callable(convert_func):
            return convert_func(value)
        return value

    def _load(self):
        """Loads xml template file.

        :return:
        """
        with open(self._template_path(), 'r') as f:
            self.stuf_message = StufMessage(f.read())

    def _template_path(self):
        """Returns absolute path to the template file

        :return:
        """
        return os.path.join(TEMPLATE_DIR, self.template)

    def time_str(self, dt: datetime.datetime):
        """Returns formatted time string

        :param dt:
        :return:
        """
        # %f returns microseconds. We want milliseconds precision, so cut off at 17 characters:
        # yyyy mm dd hh mm ss mmm = 4 + 2 + 2 + 2 + 2 + 2 + 3 = 17 characters
        return dt.strftime('%Y%m%d%H%M%S%f')[:17]

    def set_element(self, path: str, value: str):
        """Sets element value. Creates element if it doesn't exist

        :param path:
        :param value:
        :return:
        """
        full_path = self.content_root_elm + " " + path

        if self.stuf_message.find_elm(full_path) is None:
            self.stuf_message.create_elm(full_path)
        self.stuf_message.set_elm_value(full_path, value)

    def to_string(self):
        """String (XML) representation of this request. Sets tijdstip_bericht and referentienummer to
        current datetime value.

        :return:
        """
        timestr = self.time_str(datetime.datetime.utcnow().astimezone(tz=pytz.timezone(self.default_tz)))

        self.set_element(self.tijdstip_bericht_path, timestr)
        self.set_element(self.referentienummer_path, f"GOB{timestr}_{random.randint(0, sys.maxsize)}")

        return self.stuf_message.to_string()

    def params_errors(self, names, invalid_params):
        """
        If a request argument parameter(s) validation fails a params error object is returned

        :param names: the names of the failing parameters, eg ['bsn', ...]
        :param invalid_params: the specs of the failing parameters, ([{name, code, reason}, ...])
        :return:
        """
        return {
            "invalid-params": invalid_params,
            "title": "Een of meerdere parameters zijn niet correct.",
            "detail": f"De foutieve parameter(s) zijn: {', '.join(names)}.",
            "code": "paramsValidation"
        }

    def __str__(self):
        return self.to_string()

    @property
    @abstractmethod
    def template(self) -> str:
        """The XML file in the TEMPLATE_DIR that serves as basis for this request.

        :return:
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def content_root_elm(self) -> str:
        """Defines the root of the content in the XML file (serves as basis for other paths)

        :return:
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def parameter_paths(self) -> dict:
        """key -> path pairs, for example:

        {'bsn': 'BG:gelijk BG:inp.bsn'}

        :return:
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def soap_action(self) -> str:
        """SOAP action to pass in the header

        :return:
        """
        pass  # pragma: no cover
