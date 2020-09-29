import os
import shutil
import csv
import requests
import json
import datetime

from typing import List

from requests import HTTPError

from gobstuf.config import GOB_OBJECTSTORE, CONTAINER_BASE, API_INSECURE_BASE_PATH, \
    BRP_REGRESSION_TEST_APPLICATION, BRP_REGRESSION_TEST_USER, BRP_REGRESSION_TEST_LOCAL_PORT
from gobstuf.auth.routes import MKS_USER_KEY, MKS_APPLICATION_KEY

from gobconfig.datastore.config import get_datastore_config
from gobcore.datastore.factory import DatastoreFactory
from gobcore.exceptions import GOBException
from objectstore.objectstore import get_full_container_list, get_object, delete_object, put_object


class Objectstore:

    def __init__(self):
        config = get_datastore_config(GOB_OBJECTSTORE)
        datastore = DatastoreFactory.get_datastore(config)
        datastore.connect()
        self.connection = datastore.connection

    def _get_objects_list(self):
        return get_full_container_list(self.connection, CONTAINER_BASE)

    def _get_object(self, item):
        return get_object(self.connection, item, CONTAINER_BASE)

    def _delete_object(self, item):
        delete_object(self.connection, CONTAINER_BASE, item)

    def _put_object(self, name, contents, content_type):
        put_object(self.connection, CONTAINER_BASE, name, contents, content_type)

    def download_directory(self, objectstore_path: str, local_directory: str):
        objectstore_path = objectstore_path + '/' if objectstore_path[:-1] != '/' else objectstore_path
        shutil.rmtree(local_directory)
        os.makedirs(local_directory)

        for item in self._get_objects_list():
            if item['name'].startswith(objectstore_path):
                relative_path = item['name'].replace(objectstore_path, '')
                if item['content_type'] == 'application/directory':
                    os.makedirs(os.path.join(local_directory, relative_path), exist_ok=True)
                else:
                    obj = self._get_object(item)

                    save_path = os.path.join(local_directory, relative_path)
                    dst_directory = '/'.join(save_path.split('/')[:-1])
                    os.makedirs(dst_directory, exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(obj)

    def clear_directory(self, objectstore_path: str):
        for item in self._get_objects_list():
            if item['name'].startswith(objectstore_path):
                self._delete_object(item)

    def put_json_object(self, name: str, json_contents: dict):
        self._put_object(name, json.dumps(json_contents, indent=4), 'application/json')


class BrpTestCase:
    def __init__(self, id: str, description: str, endpoint: str, expected_result_file: str):
        self.id = id
        self.description = description
        self.endpoint = endpoint
        self.expected_result_file = expected_result_file

    def __eq__(self, other):
        return isinstance(other, BrpTestCase) \
               and self.id == other.id \
               and self.description == other.description \
               and self.endpoint == other.endpoint \
               and self.expected_result_file == other.expected_result_file


class BrpTestResult:
    def __init__(self, testcase: BrpTestCase):
        self.testcase = testcase
        self.expected_result = None
        self.actual_result = None
        self.errors = []


class ObjectstoreResultsWriter:
    def __init__(self, results: List[BrpTestResult], destination: str):
        self.results = results
        self.destination = destination

    def write(self):
        store = Objectstore()
        store.clear_directory(self.destination)

        results_json = {}

        for result in self.results:
            results_json[result.testcase.id] = {
                'description': result.testcase.description,
                'endpoint': result.testcase.endpoint,
                'errors': result.errors,
            }

            store.put_json_object(f"{self.destination}/{result.testcase.id}.expected.json", result.expected_result)
            store.put_json_object(f"{self.destination}/{result.testcase.id}.actual.json", result.actual_result)

        store.put_json_object(f"{self.destination}/summary.json", {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'results': results_json
        })


class BrpRegression:
    OBJECTSTORE_LOCATION = 'regression_tests/brp'
    TESTS_FILE = 'testcases.csv'
    EXPECTED_DIR = 'expected'
    DESTINATION_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'downloaded', 'brp_regression_tests')
    API_BASE = f'http://localhost:{BRP_REGRESSION_TEST_LOCAL_PORT}{API_INSECURE_BASE_PATH}'

    def __init__(self, logger):
        self.headers = {
            MKS_USER_KEY: BRP_REGRESSION_TEST_USER,
            MKS_APPLICATION_KEY: BRP_REGRESSION_TEST_APPLICATION
        }
        self.logger = logger
        self.results = []

    def _download_testfiles(self):
        os.makedirs(self.DESTINATION_DIR, exist_ok=True)
        Objectstore().download_directory(self.OBJECTSTORE_LOCATION, self.DESTINATION_DIR)

    def _load_tests(self):
        testcases = []
        with open(os.path.join(self.DESTINATION_DIR, self.TESTS_FILE), 'r') as f:
            try:
                for row, (id, description, endpoint) in enumerate(csv.reader(f)):
                    testcase = BrpTestCase(
                        id,
                        description,
                        endpoint,
                        os.path.join(self.DESTINATION_DIR, self.EXPECTED_DIR, f"{id}.json")
                    )
                    testcases.append(testcase)
            except ValueError:
                raise GOBException(f"{self.TESTS_FILE} improperly formatted. Error on line {row + 1}")
        return testcases

    def _differences(self, v1, v2, prepend_key: str):
        if isinstance(v1, dict) and isinstance(v2, dict):
            # Both dicts, check recursively
            recursive_result = self._dict_differences(v1, v2)
            # Prepend key
            return [f"{prepend_key}.{res}" for res in recursive_result]
        elif isinstance(v1, list) and isinstance(v2, list):
            return [f"{prepend_key}.{res}" for res in self._list_differences(v1, v2)]
        elif v1 != v2:
            return [prepend_key]
        else:
            return []

    def _list_differences(self, l1: list, l2: list):
        """Returns all paths of the differences in the list. Used by _dict_differences

        :param l1:
        :param l2:
        :return:
        """
        result = []

        for i in range(max(len(l1), len(l2))):
            if i >= len(l1) or i >= len(l2):
                result.append(i)
            else:
                result += self._differences(l1[i], l2[i], str(i))
        return result

    def _dict_differences(self, d1: dict, d2: dict):
        """Returns all paths of the differences between two dicts

        For example:
        d1 = {'a': {'b': {'c': 4}}, 'd': 4, 'e': 5, 'f': {'g': 7}}}
        d1 = {'a': {'b': {'c': 5}}, 'd': 4, 'e': 6, 'f': 8}
        result = ['a.b.c', 'e', 'f']

        :param d1:
        :param d2:
        :return:
        """
        result = []

        keys = set(list(d1.keys()) + list(d2.keys()))

        for key in keys:
            result += self._differences(d1.get(key), d2.get(key), key)
        return sorted(result)

    def _run_test(self, testcase: BrpTestCase) -> BrpTestResult:
        # Create new result object. Will be constructed further in this method
        result = BrpTestResult(testcase)

        r = requests.get(self.API_BASE + testcase.endpoint, headers=self.headers)

        try:
            with open(testcase.expected_result_file, 'r') as f:
                result.expected_result = json.load(f)
        except FileNotFoundError:
            result.errors.append(f"Expect file not found.")

        try:
            r.raise_for_status()
            result.actual_result = r.json()
        except HTTPError:
            result.errors.append(f"Received error from endpoint {testcase.endpoint} (status code {r.status_code})")

        if result.expected_result is not None and result.actual_result is not None:
            differences = self._dict_differences(result.expected_result, result.actual_result)

            result.errors += [f"Path does not match: {path}" for path in differences]

        return result

    def _run_tests(self, testcases: List[BrpTestCase]) -> List[BrpTestResult]:
        results = []
        for testcase in testcases:
            result = self._run_test(testcase)
            results.append(result)

            for error in result.errors:
                self.logger.error(f"Test case {result.testcase.id}: {error}")

            if not result.errors:
                self.logger.info(f"Test case {result.testcase.id}: OK")

        return results

    def run(self):
        self._download_testfiles()
        testcases = self._load_tests()
        return self._run_tests(testcases)
