from freezegun import freeze_time

from unittest import TestCase
from unittest.mock import MagicMock, patch, call, mock_open
from requests.exceptions import HTTPError

from gobstuf.regression_tests.brp import BrpRegression, Objectstore, ObjectstoreResultsWriter, BrpTestResult, BrpTestCase


class TestObjectstoreInit(TestCase):

    @patch("gobstuf.regression_tests.brp.get_datastore_config")
    @patch("gobstuf.regression_tests.brp.DatastoreFactory")
    def test_init(self, mock_ds_factory, mock_get_ds):
        store = Objectstore()
        self.assertEqual(store.connection, mock_ds_factory.get_datastore().connection)
        mock_ds_factory.get_datastore().connect.assert_called_once()


@patch("gobstuf.regression_tests.brp.get_datastore_config", MagicMock())
@patch("gobstuf.regression_tests.brp.DatastoreFactory", MagicMock())
@patch("gobstuf.regression_tests.brp.CONTAINER_BASE", "CONTAINER_BASE")
class TestObjectStore(TestCase):

    @patch("gobstuf.regression_tests.brp.get_full_container_list")
    def test_get_objects_list(self, mock_get_list):
        store = Objectstore()
        self.assertEqual(mock_get_list(), store._get_objects_list())
        mock_get_list.assert_called_with(store.connection, "CONTAINER_BASE")

    @patch("gobstuf.regression_tests.brp.get_object")
    def test_get_object(self, mock_get_object):
        store = Objectstore()
        self.assertEqual(mock_get_object(), store._get_object('some item'))
        mock_get_object.assert_called_with(store.connection, 'some item', 'CONTAINER_BASE')

    @patch("gobstuf.regression_tests.brp.delete_object")
    def test_delete_object(self, mock_delete_object):
        store = Objectstore()
        store._delete_object('some item')
        mock_delete_object.assert_called_with(store.connection, 'CONTAINER_BASE', 'some item')

    @patch("gobstuf.regression_tests.brp.put_object")
    def test_put_object(self, mock_put_object):
        store = Objectstore()
        store._put_object('some name', 'contents', 'content/type')
        mock_put_object.assert_called_with(store.connection, 'CONTAINER_BASE', 'some name', 'contents', 'content/type')

    @patch("builtins.open")
    @patch("gobstuf.regression_tests.brp.shutil.rmtree")
    @patch("gobstuf.regression_tests.brp.os.makedirs")
    def test_download_directory(self, mock_makedirs, mock_rmtree, mock_open):
        store = Objectstore()
        store._get_objects_list = MagicMock(return_value=[
            {'name': 'dira', 'content_type': 'application/directory'},
            {'name': 'dira/dirb', 'content_type': 'application/directory'},
            {'name': 'dira/dirb/filea.json', 'content_type': 'application/json'},
            {'name': 'dira/dirb/fileb.json', 'content_type': 'application/json'},
            {'name': 'dira/dirb/dire', 'content_type': 'application/directory'},
            {'name': 'dira/dirc', 'content_type': 'application/directory'},
            {'name': 'dira/dirc/filec.json', 'content_type': 'application/json'},
            {'name': 'dira/dird/filed.json', 'content_type': 'application/json'},
        ])
        store._get_object = lambda x: 'downloaded(' + x['name'] + ')'

        store.download_directory('dira/dirb', 'local/directory')

        mock_rmtree.assert_called_with('local/directory')
        mock_makedirs.assert_has_calls([
            call('local/directory'),
            call('local/directory/dire', exist_ok=True),
        ])

        mock_open.assert_has_calls([
            call('local/directory/filea.json', 'wb'),
            call('local/directory/fileb.json', 'wb'),
        ], any_order=True)

        mock_open().__enter__().write.assert_has_calls([
            call('downloaded(dira/dirb/filea.json)'),
            call('downloaded(dira/dirb/fileb.json)'),
        ], any_order=True)

    def test_clear_directory(self):
        store = Objectstore()
        store._get_objects_list = MagicMock(return_value=[
            {'name': 'a/b/c'},
            {'name': 'a/b/d'},
            {'name': 'a/b'},
            {'name': 'a'},
            {'name': 'a/e/f'},
        ])
        store._delete_object = MagicMock()
        store.clear_directory('a/b')
        store._delete_object.assert_has_calls([
            call({'name': 'a/b/c'}),
            call({'name': 'a/b/d'}),
            call({'name': 'a/b'}),
        ])

    def test_put_json_object(self):
        store = Objectstore()
        store._put_object = MagicMock()
        store.put_json_object('filename.json', {'a': 'b', 'c': {'d': 'e', 'f': 4, 'g': {'h': 4}}})

        # Should be nicely formatted
        store._put_object.assert_called_with('filename.json',
"""{
    "a": "b",
    "c": {
        "d": "e",
        "f": 4,
        "g": {
            "h": 4
        }
    }
}""", 'application/json')


class TestObjectstoreResultsWriter:

    @patch("gobstuf.regression_tests.brp.Objectstore")
    def test_write(self, mock_objectstore):
        result_list = [
            ['id1', 'description 1', '/endpoint/1', {'expected': 'result1'}, {'actual': 'result1'}, ['error1', 'error2']],
            ['id2', 'description 2', '/endpoint/2', {'expected': 'result2'}, {'actual': 'result2'}, []],
        ]

        results = []

        # Build objects
        for id, description, endpoint, expected, actual, errors in result_list:
            testcase = BrpTestCase(id, description, endpoint, 'expectedfile')
            result = BrpTestResult(testcase)
            result.expected_result = expected
            result.actual_result = actual
            result.errors = errors

            results.append(result)

        writer = ObjectstoreResultsWriter(results, 'some/destination')

        with freeze_time('2020-07-30 15:00:00'):
            writer.write()

        mock_objectstore().clear_directory.assert_called_with('some/destination')

        # Should write an 'expected' and 'actual' json for each test case, plus a summary.json
        mock_objectstore().put_json_object.assert_has_calls([
            call('some/destination/id1.expected.json', {'expected': 'result1'}),
            call('some/destination/id1.actual.json', {'actual': 'result1'}),
            call('some/destination/id2.expected.json', {'expected': 'result2'}),
            call('some/destination/id2.actual.json', {'actual': 'result2'}),
            call('some/destination/summary.json', {
                'timestamp': '2020-07-30T15:00:00',
                'results': {
                    'id1': {
                        'description': 'description 1',
                        'endpoint': '/endpoint/1',
                        'errors': ['error1', 'error2'],
                    },
                    'id2': {
                        'description': 'description 2',
                        'endpoint': '/endpoint/2',
                        'errors': [],
                    },
                },
            })
        ])


@patch("gobstuf.regression_tests.brp.BRP_REGRESSION_TEST_USER", 'TEST_USER')
@patch("gobstuf.regression_tests.brp.BRP_REGRESSION_TEST_APPLICATION", 'TEST_APPLICATION')
class TestBrpRegressionTest(TestCase):

    def test_init(self):
        logger = MagicMock()
        regr = BrpRegression(logger)
        self.assertEqual(logger, regr.logger)
        self.assertEqual([], regr.results)
        self.assertEqual({
            'MKS_GEBRUIKER': 'TEST_USER',
            'MKS_APPLICATIE': 'TEST_APPLICATION'
        }, regr.headers)

    @patch("gobstuf.regression_tests.brp.os.makedirs")
    @patch("gobstuf.regression_tests.brp.Objectstore")
    def test_download_testfiles(self, mock_objectstore, mock_makedirs):
        regr = BrpRegression(MagicMock())
        location = 'the location'
        dst_dir = 'the dst dir'
        regr.OBJECTSTORE_LOCATION = location
        regr.DESTINATION_DIR = dst_dir

        regr._download_testfiles()
        mock_objectstore().download_directory.assert_called_with(location, dst_dir)
        mock_makedirs.assert_called_with(dst_dir)

        # Try again, but now the destination dir already exists
        mock_makedirs.side_effect = FileExistsError
        regr._download_testfiles()
        mock_objectstore().download_directory.assert_called_with(location, dst_dir)
        mock_makedirs.assert_called_with(dst_dir)

    @patch("gobstuf.regression_tests.brp.os.path.join", lambda *args: "/".join(args))
    def test_load_tests(self):
        file = """\
id1,"Test case 1",/the/endpoint
id2,"Test case 2",/endpoint/2?someparameter=val&other=val2
"""

        open_mock = mock_open(read_data=file)

        open_mock.return_value.__iter__ = lambda self: self
        open_mock.return_value.__next__ = lambda self: next(iter(self.readline, ''))

        regr = BrpRegression(MagicMock())
        regr.DESTINATION_DIR = 'dst/dir'
        regr.TESTS_FILE = 'tests_file.csv'
        regr.EXPECTED_DIR = 'expected'

        with patch("builtins.open", open_mock):
            result = regr._load_tests()
        open_mock.assert_called_with("dst/dir/tests_file.csv", "r")

        expected = [
            BrpTestCase('id1', 'Test case 1', '/the/endpoint', 'dst/dir/expected/id1.json'),
            BrpTestCase('id2', 'Test case 2', '/endpoint/2?someparameter=val&other=val2', 'dst/dir/expected/id2.json')
        ]
        self.assertEqual(expected, result)

    def test_dict_differences(self):
        """Testd _dict_differences, _list_differences and _differences

        :return:
        """
        brpregr = BrpRegression(MagicMock())

        d1 = {'a': 1, 'b': 2, 'c': 3}
        d2 = {'a': 1, 'b': 3, 'c': 3}
        result = ['b']

        self.assertEqual(result, brpregr._dict_differences(d1, d2))

        d1 = {'a': 1, 'b': {'some': 'dict'}, 'c': 3}
        d2 = {'a': 1, 'b': 3, 'c': 3}
        result = ['b']

        self.assertEqual(result, brpregr._dict_differences(d1, d2))

        d1 = {'a': 1, 'b': {'some': {'nested': 'dict'}}}
        d2 = {'a': 1, 'b': {'some': {'nested': 'dict'}}}
        result = []
        self.assertEqual(result, brpregr._dict_differences(d1, d2))

        d1 = {'a': 1, 'b': {'some': {'nested': 'dict'}}}
        d2 = {'a': 1, 'b': {'some': {'other': 'dict'}}}
        result = ['b.some.nested', 'b.some.other']
        self.assertEqual(result, brpregr._dict_differences(d1, d2))
        self.assertEqual(result, brpregr._dict_differences(d2, d1))

        d1 = {'a': 1, 'b': [{'some': {'nested': 'dict'}}]}
        d2 = {'a': 1, 'b': [{'some': {'other': 'dict'}}]}
        result = ['b.0.some.nested', 'b.0.some.other']
        self.assertEqual(result, brpregr._dict_differences(d1, d2))
        self.assertEqual(result, brpregr._dict_differences(d2, d1))

        d1 = {'a': 1, 'b': {'some': {'nested': 'dict'}}}
        d2 = {'a': 1, 'b': {'some': 'str'}}
        result = ['b.some']
        self.assertEqual(result, brpregr._dict_differences(d1, d2))
        self.assertEqual(result, brpregr._dict_differences(d2, d1))

        d1 = {'a': 1, 'b': ['list', 'three', 'items']}
        d2 = {'a': 1, 'b': ['list', 'with', 'four', 'items']}
        result = ['b.1', 'b.2', 'b.3']
        self.assertEqual(result, brpregr._dict_differences(d1, d2))
        self.assertEqual(result, brpregr._dict_differences(d2, d1))

    @patch("gobstuf.regression_tests.brp.requests")
    def test_run_test(self, mock_requests):
        file = """\
{
    "some": "result",
    "with": ["a", "list"],
    "and": {
        "a": "dict"
    },
    "integer": 24,
    "bool": true
}
"""
        request_result = MagicMock()
        request_result.json.return_value = {
            "some": "result",
            "with": ["a", "list"],
            "and": {
                "a": "dict"
            },
            "integer": 24,
            "bool": True
        }

        open_mock = mock_open(read_data=file)
        mock_requests.get.return_value = request_result

        # 1. No errors, no differences
        regr = BrpRegression(MagicMock())
        regr._dict_differences = MagicMock(return_value=[])
        testcase = BrpTestCase('id', 'the description', '/the/endpoint', 'expected_result.json')
        with patch("builtins.open", open_mock):
            res = regr._run_test(testcase)
            open_mock.assert_called_with('expected_result.json', 'r')
        regr._dict_differences.assert_called_with(request_result.json.return_value, request_result.json.return_value)
        self.assertEqual(request_result.json.return_value, res.expected_result)
        self.assertEqual(request_result.json.return_value, res.actual_result)
        self.assertEqual([], res.errors)
        self.assertEqual(testcase, res.testcase)

        # 2. Have differences
        regr._dict_differences = MagicMock(return_value=['path.1', 'path.2'])
        with patch("builtins.open", open_mock):
            res = regr._run_test(testcase)
        self.assertEqual(request_result.json.return_value, res.expected_result)
        self.assertEqual(request_result.json.return_value, res.actual_result)
        self.assertEqual([
            'Path does not match: path.1',
            'Path does not match: path.2',
        ], res.errors)
        self.assertEqual(testcase, res.testcase)

        # 3. Expected result file not found and requests error
        regr._dict_differences = MagicMock(return_value=[])
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError
        mock_response.status_code = 123
        mock_requests.get.return_value = mock_response
        with patch("builtins.open", MagicMock(side_effect=FileNotFoundError)):
            res = regr._run_test(testcase)
        self.assertEqual(None, res.expected_result)
        self.assertEqual(None, res.actual_result)
        self.assertEqual([
            'Expect file not found.',
            'Received error from endpoint /the/endpoint (status code 123)'
        ], res.errors)
        self.assertEqual(testcase, res.testcase)

    def test_run_tests(self):
        mock_logger = MagicMock()
        regr = BrpRegression(mock_logger)
        regr._run_test = lambda testcase: BrpTestResult(testcase)

        cases = [
            BrpTestCase('1', '', '', ''),
            BrpTestCase('2', '', '', ''),
        ]

        def create_result(testcase, errors):
            result = BrpTestResult(testcase)
            result.errors = errors
            return result

        # Result 2 returns two errors
        results = {
            '1': lambda testcase: create_result(testcase, []),
            '2': lambda testcase: create_result(testcase, ['Error message 1', 'Error message 2'])
        }
        regr._run_test = lambda testcase: results[testcase.id](testcase)
        res = regr._run_tests(cases)
        self.assertEqual(2, len(res))
        self.assertEqual(cases[0], res[0].testcase)
        self.assertEqual(cases[1], res[1].testcase)
        mock_logger.info.assert_has_calls([
            call('Test case 1: OK'),
        ])
        mock_logger.error.assert_has_calls([
            call('Test case 2: Error message 1'),
            call('Test case 2: Error message 2'),
        ])

    def test_run(self):
        regr = BrpRegression(MagicMock())
        regr._download_testfiles = MagicMock()
        regr._load_tests = MagicMock()
        regr._run_tests = MagicMock()

        self.assertEqual(regr._run_tests.return_value, regr.run())
        regr._run_tests.assert_called_with(regr._load_tests.return_value)
