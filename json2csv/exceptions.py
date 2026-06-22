class JSON2CSVError(Exception):
    """Base exception for all json2csv conversion and structural errors."""


class FileAccessError(JSON2CSVError):
    """Raised when files or directories are missing, unreadable, or unwritable."""


class InvalidJSONFormatError(JSON2CSVError):
    """Raised when source JSON document cannot be successfully parsed by the internal engine."""


class NotAnArrayError(JSON2CSVError):
    """Raised when the root parsed element is not a JSON list/array."""


class NamespaceCollisionError(JSON2CSVError):
    """Raised when flattening a key results in a duplicate path collision."""
