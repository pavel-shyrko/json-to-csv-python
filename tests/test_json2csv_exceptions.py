import unittest
from json2csv.exceptions import (
    JSON2CSVError,
    FileAccessError,
    InvalidJSONFormatError,
    NotAnArrayError,
    NamespaceCollisionError
)

class TestExceptions(unittest.TestCase):
    def test_inheritance(self):
        """Verify the exception class hierarchy."""
        exceptions_to_test = [
            FileAccessError,
            InvalidJSONFormatError,
            NotAnArrayError,
            NamespaceCollisionError,
        ]
        for exc_cls in exceptions_to_test:
            with self.subTest(exception_class=exc_cls.__name__):
                self.assertTrue(issubclass(exc_cls, JSON2CSVError))
                self.assertTrue(issubclass(exc_cls, Exception))
        self.assertTrue(issubclass(JSON2CSVError, Exception))

    def test_exception_raising(self):
        """Verify that each exception can be raised and caught by its specific type and base type."""
        exceptions_to_test = [
            JSON2CSVError,
            FileAccessError,
            InvalidJSONFormatError,
            NotAnArrayError,
            NamespaceCollisionError,
        ]
        for exc_cls in exceptions_to_test:
            with self.subTest(raising=exc_cls.__name__):
                with self.assertRaises(exc_cls):
                    raise exc_cls()
                with self.assertRaises(JSON2CSVError):
                    raise exc_cls()

    def test_exception_chaining(self):
        """Verify that exceptions support cause chaining under Python's exception mechanisms."""
        exceptions_to_test = [
            JSON2CSVError,
            FileAccessError,
            InvalidJSONFormatError,
            NotAnArrayError,
            NamespaceCollisionError,
        ]
        for exc_cls in exceptions_to_test:
            with self.subTest(chaining=exc_cls.__name__):
                underlying = ValueError("Root error")
                with self.assertRaises(exc_cls):
                    try:
                        raise underlying
                    except ValueError as err:
                        raise exc_cls() from err
