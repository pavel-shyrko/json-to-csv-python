# Architecture State

## 1. System Overview
The **CLI JSON to CSV Converter** is a high-performance, resource-efficient command-line utility designed to transform structured and nested JSON arrays into delimited, RFC 4180-compliant CSV files. It is built strictly on the Python 3.12 Core runtime with zero third-party library dependencies.

## 2. Active Components
- **`json2csv` (Package)**: The core namespace containing the application's CLI driver and translation engine modules.
- **`json2csv.exceptions`**: The centralized error boundary of the application, isolating engine-specific and operational failures from interpreter-level panics.
- **`json2csv.converter`**: The translation and conversion module responsible for flattening hierarchical structures, parsing JSON arrays, reconciling dynamic headers, and mapping/serializing objects into 2D tabular CSV formats.

## 3. Public Interfaces & Signatures
### `json2csv.exceptions`
All custom exceptions derive from a single common application base class to enable deterministic catch-all scenarios at the entry points:

- `class JSON2CSVError(Exception)`: Base application exception class for all custom errors.
- `class FileAccessError(JSON2CSVError)`: Raised when input files or output target directories are missing, unreadable, or unwritable.
- `class InvalidJSONFormatError(JSON2CSVError)`: Raised when source JSON cannot be parsed successfully by the standard parser.
- `class NotAnArrayError(InvalidJSONFormatError)`: Raised when the root element of the source JSON document is not an array/list.
- `class NamespaceCollisionError(JSON2CSVError)`: Raised during flattening operations when duplicate target keys map to the same output field.

### `json2csv.converter`
Provides utilities for structural transformation, hierarchical flattening, and batch file translation:

- `def flatten_dict(d: dict, prefix: str = "", separator: str = ".") -> dict`:
  - **Description**: Flattens a deeply nested dictionary using a separator syntax. Keys in nested sub-dictionaries are concatenated with their parent paths using the designated separator.
  - **Inputs**:
    - `d` (dict): The target dictionary to flatten.
    - `prefix` (str): Current namespace prefix string (default: `""`).
    - `separator` (str): Namespace join character (default: `"."`).
  - **Outputs**:
    - Returns a flat single-level dictionary mapping string keys to leaf values.
  - **Exceptions**:
    - `TypeError`: If `d` is not a dict, if `prefix` or `separator` are not strings, or if any key inside is not a string.
    - `ValueError`: If circular references (cycles) are detected.
    - `NamespaceCollisionError`: If a flattened key conflicts with an existing key in the output.

- `def convert_json_to_csv(input_path: str, output_path: str, delimiter: str) -> None`:
  - **Description**: Reads a target JSON file, parses its array structure, flattens any nested objects, resolves the dynamic unified header set, and writes an RFC 4180-compliant CSV.
  - **Inputs**:
    - `input_path` (str): File system path pointing to the target JSON input file.
    - `output_path` (str): File system path pointing to the target output CSV file.
    - `delimiter` (str): Character sequence used as a CSV cell separator (must be exactly 1 char).
  - **Outputs**:
    - `None` (files written directly to disk).
  - **Exceptions**:
    - `TypeError`: If `input_path`, `output_path`, or `delimiter` are not of type `str` (or are subclassed as booleans).
    - `ValueError`: If the `delimiter` length is not exactly 1 character.
    - `FileAccessError`: If the input file is missing/unreadable, or the output target location/directory is unwritable or doesn't exist.
    - `InvalidJSONFormatError`: If the source file cannot be parsed as valid JSON.
    - `NotAnArrayError`: If the parsed JSON root structure is not a list.
    - `NamespaceCollisionError`: If structural flattening of records yields conflicting key paths.

## 4. Design Patterns & Decisions
- **Unified Exception Boundary**: By mapping all operational, format, and environment errors to subclasses of `JSON2CSVError`, the CLI driver layer can capture all anticipated engine failures cleanly. This allows the CLI to output user-friendly error messages and exit gracefully with non-zero codes, preventing internal raw Python interpreter stack traces from leaking to the shell.
- **Strict Precedence-Ordered Error Validation**: To ensure highly deterministic behavior, the conversion execution strictly follows a validated precedence sequence:
  1. Verify parameter types (raise `TypeError` on invalid arguments, excluding implicit conversions).
  2. Verify input file accessibility (raise `FileAccessError` if unreadable).
  3. Parse JSON document syntax (raise `InvalidJSONFormatError` on syntax error).
  4. Assert JSON root container structure (raise `NotAnArrayError` if not a raw list).
  5. Flatten records and detect naming clashing (raise `NamespaceCollisionError` on clashing paths).
  6. Verify output destination eligibility and write (raise `FileAccessError` if unwritable).
- **Explicit Exception Chaining**: To maintain debugging traceability and testable seams, standard library errors or root causes are intended to be chained cleanly (e.g., `raise FileAccessError("message") from original_exception`).
- **Deterministic Collision Protection**: During structural flattening, flat target keys are validated against both current outputs and original root keys before mutation. Any path overlap (such as mapping a nested structure that clashes with an existing flat key like `{"a.b": 1, "a": {"b": 2}}`) triggers an immediate `NamespaceCollisionError` to prevent silent data overwrite.
- **Identity-Based Cycle Detection**: Circular references are resolved deterministically using a visited set tracking internal object identifiers (`id(obj)`). This prevents infinite recursion during deep dictionary traversals without requiring external structural graph packages.
- **Dynamic Header Reconciliation**: Output CSV files are constructed using a dynamic union of all unique keys discovered across all objects in the flattened array. Keys are collected preserving insertion and discovery order across all records, ensuring that missing fields are gracefully written as empty cells without compromising structure.
- **Graceful Empty State Resolution**: An empty JSON array input `[]` bypasses the dynamic header compilation logic completely. It is handled as a successful edge case that writes an empty file and terminates cleanly, without throwing structural or format exceptions.

## 5. Non-Functional Invariants & Constraints
- **File Encoding**: All source, configuration, and documentation files must be explicitly encoded using UTF-8.
- **Standard Library Only**: Development is strictly restricted to the Python 3.12 Core runtime environment. Third-party packages must not be introduced as core dependencies.
- **Performance Benchmarks**: Processing a 100 megabyte (MB) flat JSON array containing 500,000 records must execute in less than 3.0 seconds.
- **Memory Envelope Rules**: Peak heap memory utilization (RSS) during execution must not exceed 2.5 times the size of the input file (e.g., maximum 250 MB heap usage for a 100 MB input file).
- **RFC 4180 Serialization**: Final CSV outputs utilize the Python `csv` module with `csv.QUOTE_MINIMAL` to enforce strict RFC 4180 rules. Double quotes, delimiters, and raw line breaks within cell contents are automatically quoted, and pre-existing quotes are escaped as `""`.
- **Stack Trace Prevention**: Raw interpreter tracebacks must be intercepted and masked at the CLI driver boundary for all anticipated logical and operational failures, translating them into human-readable console error outputs.
- **Traceability Preservation**: The exception hierarchy must accept and preserve original traceback states via explicit exception chaining.
- **Immutability of Source Data**: Traversal operations must be strictly read-only relative to their input datasets. The original dictionaries passed to the flattening engine must not be mutated, augmented, or restructured in-place.
- **Structural Sequence Preservation**: Arrays, sequences, or lists of objects and primitives inside dictionaries must remain intact as raw array structures. The flattening engine must not unpack or flatten arrays into indexed sub-keys, preserving them for raw serialization during final CSV writing.