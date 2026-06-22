import argparse
import sys

from json2csv.converter import convert_json_to_csv
from json2csv.exceptions import (
    FileAccessError,
    InvalidJSONFormatError,
    NamespaceCollisionError,
    NotAnArrayError,
)


def main(args: list[str] | None = None) -> int:
    """
    Parses CLI arguments, resolves the delimiter, executes the converter, and handles errors.

    Args:
        args: Optional list of command-line arguments. Defaults to None (which falls back to sys.argv[1:]).

    Returns:
        int: Exit code (0 for success, 1 for validation/format/syntax/collision errors, 2 for file access/IO errors).
    """
    if args is not None:
        if not (isinstance(args, list) and not isinstance(args, bool)):
            raise TypeError(f"args must be a list, got {type(args).__name__!r}")
        for item in args:
            if not (isinstance(item, str) and not isinstance(item, bool)):
                raise TypeError(f"all args elements must be str, got {type(item).__name__!r}")

    parser = argparse.ArgumentParser(
        description="Convert a JSON array file to a CSV file."
    )
    parser.add_argument("input_file", help="Path to the input JSON file.")
    parser.add_argument("output_file", help="Path to the output CSV file.")
    parser.add_argument(
        "-d",
        "--delimiter",
        default=",",
        help="Field delimiter character (default: ',').",
    )

    parsed = parser.parse_args(args)

    try:
        delimiter = parsed.delimiter.encode("utf-8").decode("unicode_escape")
    except (UnicodeDecodeError, ValueError) as exc:
        print(f"Error: invalid delimiter escape sequence: {exc}", file=sys.stderr)
        return 1

    if len(delimiter) != 1:
        print(
            f"Error: delimiter must be exactly 1 character, got {len(delimiter)!r} characters: {parsed.delimiter!r}",
            file=sys.stderr,
        )
        return 1

    try:
        convert_json_to_csv(parsed.input_file, parsed.output_file, delimiter)
    except FileAccessError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (InvalidJSONFormatError, NotAnArrayError, NamespaceCollisionError, TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
