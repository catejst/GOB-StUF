from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.rest.brp.argument_checks import ArgumentCheck
from gobstuf.reference_data.code_resolver import DataItemNotFoundException

class TestArgumentCheck(TestCase):

    def test_validate(self):
        check = ArgumentCheck.is_boolean
        for v in ['true', 'false']:
            self.assertIsNone(ArgumentCheck.validate(check, v))
        for v in ['True', 'False', 'TRUE', 'FALSE', '', '1', '0', 't', 'f']:
            self.assertEqual(ArgumentCheck.validate(check, v), check)

        check = ArgumentCheck.is_postcode
        for v in ['1234AB', '9999XX']:
            self.assertIsNone(ArgumentCheck.validate(check, v))
        for v in ['1234ab', '123456', '1234 AB', '']:
            self.assertEqual(ArgumentCheck.validate(check, v), check)

        check = ArgumentCheck.is_integer
        for v in ['0', '1']:
            self.assertIsNone(ArgumentCheck.validate(check, v))
        for v in ['-1', '', '1.5', 'one']:
            self.assertEqual(ArgumentCheck.validate(check, v), check)

        check = ArgumentCheck.is_positive_integer
        for v in ['1', '100']:
            self.assertIsNone(ArgumentCheck.validate(check, v))
        for v in ['0', '-1', '', '1.5', 'one']:
            self.assertEqual(ArgumentCheck.validate(check, v), check)

        check = [ArgumentCheck.is_integer, ArgumentCheck.is_positive_integer]
        for v in ['1', '100']:
            self.assertIsNone(ArgumentCheck.validate(check, v))
        for v in ['-1', '', '1.5', 'one']:
            self.assertEqual(ArgumentCheck.validate(check, v), ArgumentCheck.is_integer)
        for v in ['0']:
            self.assertEqual(ArgumentCheck.validate(check, v), ArgumentCheck.is_positive_integer)

        check = ArgumentCheck.is_valid_date_format
        self.assertIsNone(ArgumentCheck.validate(check, '2020-05-28'))

        check = ArgumentCheck.is_valid_date
        self.assertIsNone(ArgumentCheck.validate(check, '2020-02-28'))
        self.assertTrue(ArgumentCheck.validate(check, '2020-02-30'))

        check = ArgumentCheck.has_min_length(20)
        for v in [19*'a', '', 'a', 'aaa']:
            self.assertEqual(ArgumentCheck.validate(check, v), check)
        for v in [20*'a', 100*'a', 21*'a']:
            self.assertIsNone(ArgumentCheck.validate(check, v))

        check = ArgumentCheck.has_max_length(20)
        for v in [20*'a', '', 5*'a', 'jkaldjf']:
            self.assertIsNone(ArgumentCheck.validate(check, v))
        for v in [21*'a', 100*'a']:
            self.assertEqual(ArgumentCheck.validate(check, v), check)

    @patch('gobstuf.rest.brp.argument_checks.CodeResolver')
    def test_validate_gemeente(self, mock_code_resolver):
        mock_code_resolver.get_gemeente_code.side_effect = ['any code', DataItemNotFoundException()]

        check = ArgumentCheck.is_valid_gemeente

        self.assertIsNone(ArgumentCheck.validate(check, 'any gemeente'))
        self.assertTrue(ArgumentCheck.validate(check, 'invalid gemeente'))
