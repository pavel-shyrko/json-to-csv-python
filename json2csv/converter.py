import csv
import json
import os

from json2csv.exceptions import (
    FileAccessError,
    InvalidJSONFormatError,
    NamespaceCollisionError,
    NotAnArrayError,
)


def convert_json_to_csv(input_path: str, output_path: str, delimiter: str) -> None:
    """
    Reads, parses, flattens, and translates target JSON files to CSV files.

    Args:
        input_path (str): File system path to the input JSON file.
        output_path (str): File system path to the output CSV file.
        delimiter (str): Cell separator character sequence (must be exactly 1 char).

    Raises:
        TypeError: If input parameters are not of type str.
        FileAccessError: If input/output files or paths are inaccessible.
        InvalidJSONFormatError: If the file cannot be parsed as valid JSON.
        NotAnArrayError: If parsed JSON root is not a list.
        NamespaceCollisionError: If structural flattening results in duplicated keys.
    """
    if not isinstance(input_path, str) or isinstance(input_path, bool):
        raise TypeError(f"input_path must be str, got {type(input_path).__name__}")
    if not isinstance(output_path, str) or isinstance(output_path, bool):
        raise TypeError(f"output_path must be str, got {type(output_path).__name__}")
    if not isinstance(delimiter, str) or isinstance(delimiter, bool):
        raise TypeError(f"delimiter must be str, got {type(delimiter).__name__}")

    if len(delimiter) != 1:
        raise ValueError(
            f"delimiter must be exactly 1 character, got length {len(delimiter)}"
        )

    try:
        with open(input_path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as err:
        raise FileAccessError(f"Cannot read input file '{input_path}'") from err

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as err:
        raise InvalidJSONFormatError(f"Failed to parse JSON: {err}") from err

    if not isinstance(data, list):
        raise NotAnArrayError(
            f"JSON root must be a list, got {type(data).__name__}"
        )

    if not data:
        output_dir = os.path.dirname(output_path) or "."
        if not os.path.isdir(output_dir):
            raise FileAccessError(
                f"Output directory does not exist: '{output_dir}'"
            )
        try:
            with open(output_path, "w", encoding="utf-8"):
                pass
        except OSError as err:
            raise FileAccessError(f"Cannot write output file '{output_path}'") from err
        return

    flattened_rows: list[dict] = []
    headers_ordered: list[str] = []
    headers_seen: set[str] = set()

    for record in data:
        flat = flatten_dict(record)
        flattened_rows.append(flat)
        for key in flat:
            if key not in headers_seen:
                headers_ordered.append(key)
                headers_seen.add(key)

    output_dir = os.path.dirname(output_path) or "."
    if not os.path.isdir(output_dir):
        raise FileAccessError(f"Output directory does not exist: '{output_dir}'")

    try:
        with open(output_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=headers_ordered,
                delimiter=delimiter,
                quoting=csv.QUOTE_MINIMAL,
                extrasaction="ignore",
                restval="",
            )
            writer.writeheader()
            writer.writerows(flattened_rows)
    except OSError as err:
        raise FileAccessError(f"Cannot write output file '{output_path}'") from err


def flatten_dict(d: dict, prefix: str = "", separator: str = ".") -> dict:
    """
    Flattens a deeply nested dictionary using a separator syntax.

    Args:
        d (dict): The dictionary to flatten.
        prefix (str): Current namespace prefix.
        separator (str): Namespace join character.

    Returns:
        dict: A flat single-level dictionary mapping string keys to leaf values.

    Raises:
        TypeError: If `d` is not a dict, if `prefix`/`separator` are not strings, or if any key inside is not a string.
        ValueError: If circular references (cycles) are detected.
        NamespaceCollisionError: If a flattened key conflicts with an existing key in the output.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Expected dict, got {type(d).__name__}")
    if not isinstance(prefix, str) or isinstance(prefix, bool):
        raise TypeError(f"Expected str for prefix, got {type(prefix).__name__}")
    if not isinstance(separator, str) or isinstance(separator, bool):
        raise TypeError(f"Expected str for separator, got {type(separator).__name__}")

    _validate_types(d, {id(d)})

    result: dict = {}
    _flatten_recursive(d, prefix, separator, result, set(), d, is_root=True)
    return result


def _validate_types(d: dict, visited: set) -> None:
    if not isinstance(d, dict):
        raise TypeError(f"Expected dict, got {type(d).__name__}")
    for key, value in d.items():
        if not isinstance(key, str) or isinstance(key, bool):
            raise TypeError(f"All keys must be strings, got {type(key).__name__}")
        if isinstance(value, dict):
            val_id = id(value)
            if val_id not in visited:
                _validate_types(value, visited | {val_id})


def _flatten_recursive(
    d: dict,
    prefix: str,
    separator: str,
    result: dict,
    visited: set,
    d_root: dict,
    is_root: bool = False,
) -> None:
    obj_id = id(d)
    if obj_id in visited:
        raise ValueError("Circular reference detected in input dictionary")
    visited = visited | {obj_id}

    for key, value in d.items():
        if not isinstance(key, str) or isinstance(key, bool):
            raise TypeError(f"All keys must be strings, got {type(key).__name__}")

        if is_root and prefix == "":
            flat_key = key
        else:
            flat_key = f"{prefix}{separator}{key}"

        if flat_key in result:
            raise NamespaceCollisionError(
                f"Key namespace collision detected: '{flat_key}'"
            )
        if flat_key in d_root and flat_key != key:
            raise NamespaceCollisionError(
                f"Key namespace collision detected: '{flat_key}'"
            )

        if isinstance(value, dict):
            _flatten_recursive(value, flat_key, separator, result, visited, d_root, is_root=False)
        else:
            if flat_key in result:
                raise NamespaceCollisionError(
                    f"Key namespace collision detected: '{flat_key}'"
                )
            result[flat_key] = value
