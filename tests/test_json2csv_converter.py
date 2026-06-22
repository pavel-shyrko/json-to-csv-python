import unittest
from json2csv.exceptions import NamespaceCollisionError
from json2csv.converter import flatten_dict

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
                actual = flatten_dict(d, prefix=prefix, separator=separator)
                self.assertEqual(actual, expected)

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
            ("d is None", None, "", ".", TypeError),
            ("d is a list", [1, 2, 3], "", ".", TypeError),
            ("d is a string", "not a dict", "", ".", TypeError),
            ("prefix is not a string (int)", {}, 123, ".", TypeError),
            ("prefix is not a string (bool)", {}, True, ".", TypeError),
            ("prefix is not a string (None)", {}, None, ".", TypeError),
            ("separator is not a string (int)", {}, "", 42, TypeError),
            ("separator is not a string (None)", {}, "", None, TypeError),
            ("root key is integer", {123: "val"}, "", ".", TypeError),
            ("root key is boolean (subclass of int)", {True: "val"}, "", ".", TypeError),
            ("root key is None", {None: "val"}, "", ".", TypeError),
            ("nested key is integer", {"a": {456: "val"}}, "", ".", TypeError),
            ("nested key is boolean", {"a": {False: "val"}}, "", ".", TypeError),
            ("nested key is None", {"a": {None: "val"}}, "", ".", TypeError),
        ]
        
        for name, d, prefix, separator, expected_exc in test_cases:
            with self.subTest(case=name):
                with self.assertRaises(expected_exc):
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
