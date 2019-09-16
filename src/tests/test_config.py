import unittest
from unittest import mock

from gobstuf.config import _getenv

class TestConfig(unittest.TestCase):

    @mock.patch("os.getenv")
    def test_getenv_notset(self, mock_getenv):
        mock_getenv.side_effect = lambda varname, value=None: value

        # Test for variable that is not set
        with self.assertRaises(AssertionError):
            _getenv("SOME UNKNOWN VARIABLE")

        # Test for optional value
        value = _getenv("UNSET VARIABLE", is_optional=True)
        self.assertIsNone(value)

        # Test for variable is not set but default value is given
        value = _getenv("SOME UNKNOWN VARIABLE", "DEFAULT VALUE")
        self.assertEqual(value, "DEFAULT VALUE")

    @mock.patch("os.getenv")
    def test_getenv_set(self, mock_getenv):
        mock_getenv.side_effect = lambda varname, value=None: "value"

        # Test for variable that is set
        value = _getenv("SOME KNOWN VARIABLE")
        self.assertEqual(value, "value")

        # But empty values are not allowed

        mock_getenv.side_effect = lambda varname, value=None: ""

        # Not as default value
        with self.assertRaises(AssertionError):
            _getenv("SOME KNOWN VARIABLE", "")

        # Not as variable value
        with self.assertRaises(AssertionError):
            _getenv("SOME KNOWN VARIABLE")
