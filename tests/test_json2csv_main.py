import unittest
from unittest.mock import patch
from json2csv.main import main
from json2csv.exceptions import (
    FileAccessError,
    InvalidJSONFormatError,
    NotAnArrayError,
    NamespaceCollisionError,
)

class TestJSON2CSVMain(unittest.TestCase):
    def test_main_type_boundaries(self):
        invalid_args = [
            123,
            True,
            False,
            "not-a-list",
            {"key": "val"},
            [123, "out.csv"],
            ["in.json", None],
            ["in.json", "out.csv", 1],
            ["in.json", "out.csv", True],
        ]
        for idx, val in enumerate(invalid_args):
            with self.subTest(case=idx, val=val):
                with self.assertRaises(TypeError):
                    main(val)

    @patch("sys.argv", ["main.py", "in.json", "out.csv"])
    @patch("json2csv.main.convert_json_to_csv")
    def test_main_default_args(self, mock_convert):
        result = main(None)
        self.assertEqual(result, 0)
        mock_convert.assert_called_once_with("in.json", "out.csv", ",")

    @patch("json2csv.main.convert_json_to_csv")
    def test_main_delimiter_validation_precedence(self, mock_convert):
        cases = [
            ["nonexistent.json", "out.csv", "-d", "ab"],
            ["nonexistent.json", "out.csv", "--delimiter", "ab"],
            ["nonexistent.json", "out.csv", "-d", ""],
            ["nonexistent.json", "out.csv", "--delimiter", ""],
            ["nonexistent.json", "out.csv", "-d", "\\t\\n"],
            ["nonexistent.json", "out.csv", "--delimiter", "\\t\\n"],
            ["nonexistent.json", "out.csv", "-d", "too_long_delimiter"],
        ]
        for idx, args in enumerate(cases):
            with self.subTest(case=idx, args=args):
                mock_convert.reset_mock()
                result = main(args)
                self.assertEqual(result, 1)
                mock_convert.assert_not_called()

    @patch("json2csv.main.convert_json_to_csv")
    def test_main_delimiter_valid_escapes(self, mock_convert):
        cases = [
            (["in.json", "out.csv", "-d", "\\t"], "\t"),
            (["in.json", "out.csv", "--delimiter", "\\n"], "\n"),
            (["in.json", "out.csv", "-d", "\\r"], "\r"),
            (["in.json", "out.csv", "--delimiter", "\\\\"], "\\"),
        ]
        for idx, (args, expected_delim) in enumerate(cases):
            with self.subTest(case=idx, args=args):
                mock_convert.reset_mock()
                result = main(args)
                self.assertEqual(result, 0)
                mock_convert.assert_called_once_with("in.json", "out.csv", expected_delim)

    @patch("json2csv.main.convert_json_to_csv")
    def test_main_exception_handling(self, mock_convert):
        cases = [
            (FileAccessError(), 2),
            (InvalidJSONFormatError(), 1),
            (NotAnArrayError(), 1),
            (NamespaceCollisionError(), 1),
            (TypeError(), 1),
            (ValueError(), 1),
        ]
        for idx, (exception_inst, expected_code) in enumerate(cases):
            with self.subTest(case=idx, exception=type(exception_inst).__name__):
                mock_convert.reset_mock()
                mock_convert.side_effect = exception_inst
                result = main(["in.json", "out.csv"])
                self.assertEqual(result, expected_code)
                mock_convert.assert_called_once()

    @patch("json2csv.main.convert_json_to_csv")
    def test_main_invalid_argument_syntax(self, mock_convert):
        cases = [
            [],
            ["only_one_argument.json"],
            ["-d", ","],
        ]
        for idx, args in enumerate(cases):
            with self.subTest(case=idx, args=args):
                mock_convert.reset_mock()
                try:
                    result = main(args)
                    self.assertNotEqual(result, 0)
                except SystemExit as e:
                    self.assertNotEqual(e.code, 0)
                mock_convert.assert_not_called()
