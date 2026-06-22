import os
import tempfile
import unittest
from json2csv.exceptions import (
    FileAccessError,
    InvalidJSONFormatError,
    NotAnArrayError,
    NamespaceCollisionError,
)
from json2csv.converter import convert_json_to_csv, flatten_dict

class TestFlattenDict(unittest.TestCase):
    def test_valid_flattening_scenarios(self):
        """Test valid dictionary inputs and check correct flattened outputs."""
        test_cases = [
            ("empty dict", {}, "", ".", {}),
            ("flat dict", {"name": "Alice", "age": 30}, "", ".", {"name": "Alice", "age": 30}),
            ("nested dict", {"user": {"profile": {"name": "Bob"}}}, "", ".", {"user.profile.name": "Bob"}),
            ("custom separator", {"user": {"id": 101}}, "", "/", {"user/id": 101}),
            ("custom prefix", {"id": 101}, "root", ".", {"root.id": 101}),
            ("custom prefix and separator", {"id": 101}, "root", "/", {"root/id": 101}),
            ("none and list values", {"items": [1, 2, 3], "meta": None}, "", ".", {"items": [1, 2, 3], "meta": None}),
            ("empty string key", {"": {"inner": "val"}}, "", ".", {".inner": "val"}),
            ("multiple types of leaves", {"b": True, "f": 12.34, "i": 42, "s": "str"}, "", ".", {"b": True, "f": 12.34, "i": 42, "s": "str"}),
            ("multiple branches", {"a": {"x": 1}, "b": {"y": 2, "z": {"w": 3}}}, "", ".", {"a.x": 1, "b.y": 2, "b.z.w": 3}),
        ]
        
        for name, d, prefix, separator, expected in test_cases:
            with self.subTest(case=name):
                d_copy = d.copy() if hasattr(d, "copy") else d
                actual = flatten_dict(d, prefix=prefix, separator=separator)
                self.assertEqual(actual, expected)
                self.assertEqual(d, d_copy)

    def test_dag_no_cycle(self):
        """Test that a directed acyclic graph (shared references without cycles) flattens successfully."""
        shared = {"leaf": "value"}
        d = {"branch_a": shared, "branch_b": shared}
        expected = {"branch_a.leaf": "value", "branch_b.leaf": "value"}
        actual = flatten_dict(d)
        self.assertEqual(actual, expected)

    def test_type_errors(self):
        """Test that invalid types for d, prefix, separator, or dictionary keys raise TypeError."""
        test_cases = [
            ("d is None", None, "", "."),
            ("d is a list", [1, 2, 3], "", "."),
            ("d is a string", "not a dict", "", "."),
            ("prefix is not a string (int)", {}, 123, "."),
            ("prefix is not a string (bool)", {}, True, "."),
            ("prefix is not a string (None)", {}, None, "."),
            ("separator is not a string (int)", {}, "", 42),
            ("separator is not a string (None)", {}, "", None),
            ("root key is integer", {123: "val"}, "", "."),
            ("root key is boolean (subclass of int)", {True: "val"}, "", "."),
            ("root key is None", {None: "val"}, "", "."),
            ("nested key is integer", {"a": {456: "val"}}, "", "."),
            ("nested key is boolean", {"a": {False: "val"}}, "", "."),
            ("nested key is None", {"a": {None: "val"}}, "", "."),
        ]
        
        for name, d, prefix, separator in test_cases:
            with self.subTest(case=name):
                with self.assertRaises(TypeError):
                    flatten_dict(d, prefix=prefix, separator=separator)

    def test_namespace_collisions(self):
        """Test that namespace collisions raise NamespaceCollisionError."""
        test_cases = [
            ("simple collision", {"a.b": 1, "a": {"b": 2}}, "", "."),
            ("simple collision reversed key order", {"a": {"b": 2}, "a.b": 1}, "", "."),
            ("custom separator collision", {"a_b": 1, "a": {"b": 2}}, "", "_"),
            ("collision with prefix", {"root.a": 1, "a": 2}, "root", "."),
            ("nested multi-level collision", {"a.b.c": 1, "a": {"b": {"c": 3}}}, "", "."),
        ]
        
        for name, d, prefix, separator in test_cases:
            with self.subTest(case=name):
                with self.assertRaises(NamespaceCollisionError):
                    flatten_dict(d, prefix=prefix, separator=separator)

    def test_circular_references(self):
        """Test that circular references trigger ValueError."""
        d_simple = {}
        d_simple["self"] = d_simple
        
        d_nested = {"a": {"b": {}}}
        d_nested["a"]["b"]["cycle"] = d_nested
        
        d_deep = {"x": {"y": {"z": {}}}}
        d_deep["x"]["y"]["z"]["back"] = d_deep["x"]

        test_cases = [
            ("simple cycle", d_simple),
            ("nested cycle", d_nested),
            ("deep cycle", d_deep),
        ]
        
        for name, d in test_cases:
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    flatten_dict(d)

    def test_precedence_of_exceptions(self):
        """Verify that any type validation error is raised before any structural validation error."""
        cycle_with_invalid_key = {}
        cycle_with_invalid_key["self"] = cycle_with_invalid_key
        cycle_with_invalid_key[123] = "error"
        
        collision_with_invalid_key = {"a.b": 1, "a": {"b": 2}, None: "error"}
        
        collision_and_cycle = {"a.b": 1, "a": {}}
        collision_and_cycle["a"]["b"] = collision_and_cycle
        
        with self.subTest(case="cycle with invalid key type"):
            with self.assertRaises(TypeError):
                flatten_dict(cycle_with_invalid_key)
                
        with self.subTest(case="collision with invalid key type"):
            with self.assertRaises(TypeError):
                flatten_dict(collision_with_invalid_key)
                
        with self.subTest(case="invalid prefix parameter with collision and cycle"):
            with self.assertRaises(TypeError):
                flatten_dict(collision_and_cycle, prefix=123)


class TestConvertJsonToCsv(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.temp_dir.name, "input.json")
        self.output_path = os.path.join(self.temp_dir.name, "output.csv")

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_input(self, content: str):
        with open(self.input_path, "w", encoding="utf-8") as f:
            f.write(content)

    def read_output(self) -> str:
        with open(self.output_path, "r", encoding="utf-8", newline="") as f:
            return f.read()

    def test_argument_types(self):
        """Test that invalid argument types raise TypeError."""
        test_cases = [
            ("input_path is not str", 123, self.output_path, ","),
            ("output_path is not str", self.input_path, 123, ","),
            ("delimiter is not str", self.input_path, self.output_path, 42),
            ("input_path is None", None, self.output_path, ","),
            ("output_path is None", self.input_path, None, ","),
            ("delimiter is None", self.input_path, self.output_path, None),
            ("input_path is bool", True, self.output_path, ","),
        ]
        for name, in_p, out_p, delim in test_cases:
            with self.subTest(case=name):
                with self.assertRaises(TypeError):
                    convert_json_to_csv(in_p, out_p, delim)

    def test_delimiter_validation(self):
        """Test delimiter bounds: must be exactly 1 char."""
        test_cases = [
            ("empty delimiter", ""),
            ("multi-char delimiter", ",,"),
        ]
        for name, delim in test_cases:
            with self.subTest(case=name):
                self.write_input("[]")
                with self.assertRaises((ValueError, TypeError)):
                    convert_json_to_csv(self.input_path, self.output_path, delim)

    def test_file_access_errors(self):
        """Test FileAccessError for unreadable input path and unwritable output locations."""
        non_existent_input = os.path.join(self.temp_dir.name, "does_not_exist.json")
        with self.subTest(case="input file does not exist"):
            with self.assertRaises(FileAccessError):
                convert_json_to_csv(non_existent_input, self.output_path, ",")

        self.write_input("[]")
        unwritable_output = os.path.join(self.temp_dir.name, "nonexistent_subfolder", "out.csv")
        with self.subTest(case="output directory does not exist"):
            with self.assertRaises(FileAccessError):
                convert_json_to_csv(self.input_path, unwritable_output, ",")

    def test_invalid_json_format(self):
        """Test InvalidJSONFormatError for raw syntactic parsing failures."""
        test_cases = [
            ("empty file", ""),
            ("invalid bracket closure", "["),
            ("unclosed brace", "[{]"),
            ("trailing comma", '[{"a": 1},]'),
            ("naked string", '"not json list"'),
            ("malformed nested", '[{"a": {"b": }}]'),
        ]
        for name, content in test_cases:
            with self.subTest(case=name):
                self.write_input(content)
                with self.assertRaises(InvalidJSONFormatError):
                    convert_json_to_csv(self.input_path, self.output_path, ",")

    def test_not_an_array_error(self):
        """Test NotAnArrayError when parsed JSON root is not a list."""
        test_cases = [
            ("root is object", '{"a": 1}'),
            ("root is integer", '42'),
            ("root is boolean", 'true'),
            ("root is null", 'null'),
            ("root is string", '"hello"'),
        ]
        for name, content in test_cases:
            with self.subTest(case=name):
                self.write_input(content)
                with self.assertRaises(NotAnArrayError):
                    convert_json_to_csv(self.input_path, self.output_path, ",")

    def test_namespace_collision_in_conversion(self):
        """Test NamespaceCollisionError during structural flattening."""
        test_cases = [
            ("collision in array element", '[{"a": {"b": 1}, "a.b": 2}]'),
            ("collision in secondary element", '[{"x": 1}, {"a": {"b": 1}, "a.b": 2}]'),
        ]
        for name, content in test_cases:
            with self.subTest(case=name):
                self.write_input(content)
                with self.assertRaises(NamespaceCollisionError):
                    convert_json_to_csv(self.input_path, self.output_path, ",")

    def test_error_precedence(self):
        """Verify strict error precedence bounds."""
        with self.subTest(case="TypeError has precedence over FileAccessError (input missing)"):
            with self.assertRaises(TypeError):
                convert_json_to_csv(123, "out.csv", ",")

        non_existent_input = os.path.join(self.temp_dir.name, "no_such_file.json")
        with self.subTest(case="FileAccessError (input missing) has precedence over InvalidJSONFormatError"):
            with self.assertRaises(FileAccessError):
                convert_json_to_csv(non_existent_input, self.output_path, ",")

        self.write_input("{")
        with self.subTest(case="InvalidJSONFormatError has precedence over NotAnArrayError"):
            with self.assertRaises(InvalidJSONFormatError):
                convert_json_to_csv(self.input_path, self.output_path, ",")

        self.write_input('{"a": {"b": 1}, "a.b": 2}')
        with self.subTest(case="NotAnArrayError has precedence over NamespaceCollisionError"):
            with self.assertRaises(NotAnArrayError):
                convert_json_to_csv(self.input_path, self.output_path, ",")

        self.write_input('[{"a": {"b": 1}, "a.b": 2}]')
        unwritable_output = os.path.join(self.temp_dir.name, "nonexistent_subfolder", "out.csv")
        with self.subTest(case="NamespaceCollisionError has precedence over FileAccessError (unwritable output)"):
            with self.assertRaises(NamespaceCollisionError):
                convert_json_to_csv(self.input_path, unwritable_output, ",")

    def test_valid_conversions(self):
        """Test valid conversion cases and RFC 4180 compatibility."""
        test_cases = [
            (
                "empty array",
                '[]',
                ''
            ),
            (
                "simple flat array",
                '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]',
                'name,age\r\nAlice,30\r\nBob,25\r\n'
            ),
            (
                "nested structures",
                '[{"user": {"name": "Alice", "info": {"age": 30}}}]',
                'user.name,user.info.age\r\nAlice,30\r\n'
            ),
            (
                "heterogeneous array elements",
                '[{"a": 1}, {"b": 2, "a": 3}]',
                'a,b\r\n1,\r\n3,2\r\n'
            ),
            (
                "custom delimiter (semicolon)",
                '[{"name": "Alice", "age": 30}]',
                'name;age\r\nAlice;30\r\n'
            )
        ]

        for name, json_content, expected_csv in test_cases:
            with self.subTest(case=name):
                self.write_input(json_content)
                delim = ";" if "semicolon" in name else ","
                convert_json_to_csv(self.input_path, self.output_path, delim)
                actual_csv = self.read_output()

                norm_actual = actual_csv.replace("\r\n", "\n")
                norm_expected = expected_csv.replace("\r\n", "\n")

                if not json_content or json_content == '[]':
                    self.assertIn(norm_actual, ["", "\n"])
                else: 
                    actual_lines = [line.strip() for line in norm_actual.strip().split("\n") if line.strip()]
                    expected_lines = [line.strip() for line in norm_expected.strip().split("\n") if line.strip()]
                    self.assertEqual(len(actual_lines), len(expected_lines))
                    
                    actual_headers = set(actual_lines[0].split(delim))
                    expected_headers = set(expected_lines[0].split(delim))
                    self.assertEqual(actual_headers, expected_headers)

                    actual_header_list = actual_lines[0].split(delim)
                    expected_header_list = expected_lines[0].split(delim)

                    for i in range(1, len(expected_lines)):
                        act_vals = dict(zip(actual_header_list, actual_lines[i].split(delim)))
                        exp_vals = dict(zip(expected_header_list, expected_lines[i].split(delim)))
                        act_vals = {k: v for k, v in act_vals.items() if v != ""}
                        exp_vals = {k: v for k, v in exp_vals.items() if v != ""}
                        self.assertEqual(act_vals, exp_vals)
