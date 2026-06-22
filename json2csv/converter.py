from json2csv.exceptions import NamespaceCollisionError


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
