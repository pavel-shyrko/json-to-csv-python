# Architecture State

## 1. System Overview
The **CLI JSON to CSV Converter** is a high-performance, resource-efficient command-line utility designed to transform structured and nested JSON arrays into delimited, RFC 4180-compliant CSV files. It is built strictly on the Python 3.12 Core runtime with zero third-party library dependencies.

## 2. Active Components
- **`json2csv` (Package)**: The core namespace containing the application's CLI driver and translation engine modules.
- **`json2csv.exceptions`**: The centralized error boundary of the application, isolating engine-specific and operational failures from interpreter-level panics.
- **`json2csv.converter`**: The translation and conversion module responsible for flattening hierarchical structures and mapping objects into 2D tabular formats.

## 3. Public Interfaces & Signatures
### `json2csv.exceptions`
All custom exceptions derive from a single common application base class to enable deterministic catch-all scenarios at the entry points:

- `class JSON2CSVError(Exception)`: Base application exception class for all custom errors.
- `class FileAccessError(JSON2CSVError)`: Raised when input files or output target directories are missing, unreadable, or unwritable.
- `class InvalidJSONFormatError(JSON2CSVError)`: Raised when source JSON cannot be parsed successfully by the standard parser.
- `class NotAnArrayError(JSON2CSVError)`: Raised when the root element of the source JSON document is not an array/list.
- `class NamespaceCollisionError(JSON2CSVError)`: Raised during flattening operations when duplicate target keys map to the same output field.

### `json2csv.converter`
Provides utilities for structural transformation and flattening of JSON-like dictionary hierarchies:

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

## 4. Design Patterns & Decisions
- **Unified Exception Boundary**: By mapping all operational, format, and environment errors to subclasses of `JSON2CSVError`, the CLI driver layer can capture all anticipated engine failures cleanly. This allows the CLI to output user-friendly error messages and exit gracefully with non-zero codes, preventing internal raw Python interpreter stack traces from leaking to the shell.
- **Explicit Exception Chaining**: To maintain debugging traceability and testable seams, standard library errors or root causes are intended to be chained cleanly (e.g., `raise FileAccessError("message") from original_exception`).
- **Deterministic Collision Protection**: During structural flattening, flat target keys are validated against both current outputs and original root keys before mutation. Any path overlap (such as mapping a nested structure that clashes with an existing flat key like `{"a.b": 1, "a": {"b": 2}}`) triggers an immediate `NamespaceCollisionError` to prevent silent data overwrite.
- **Identity-Based Cycle Detection**: Circular references are resolved deterministically using a visited set tracking internal object identifiers (`id(obj)`). This prevents infinite recursion during deep dictionary traversals without requiring external structural graph packages.
- **Precedence-Ordered Type Validation**: To ensure type safety, the system executes strict input contract validation (checking key/value base types and checking that all keys in the hierarchy are strictly strings) *before* processing any structural operations or raising namespace-related errors.

## 5. Non-Functional Invariants & Constraints
- **File Encoding**: All source, configuration, and documentation files must be explicitly encoded using UTF-8.
- **Standard Library Only**: Development is strictly restricted to the Python 3.12 Core runtime environment. Third-party packages must not be introduced as core dependencies.
- **Stack Trace Prevention**: Raw interpreter tracebacks must be intercepted and masked at the CLI driver boundary for all anticipated logical and operational failures, translating them into human-readable console error outputs.
- **Traceability Preservation**: The exception hierarchy must accept and preserve original traceback states via explicit exception chaining.
- **Immutability of Source Data**: Traversal operations must be strictly read-only relative to their input datasets. The original dictionaries passed to the flattening engine must not be mutated, augmented, or restructured in-place.
- **Structural Sequence Preservation**: Arrays, sequences, or lists of objects and primitives inside dictionaries must remain intact as raw array structures. The flattening engine must not unpack or flatten arrays into indexed sub-keys, preserving them for raw serialization during final CSV writing.