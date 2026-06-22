# CLI JSON to CSV Converter

A high-performance, resource-efficient command-line utility that transforms structured and nested JSON array files into delimited RFC 4180-compliant CSV files.

## Features
- **Standard Flat JSON Array Conversion**: Parse uniform or non-uniform flat JSON arrays into standard comma-separated CSV rows with auto-generated unified headers.
- **Configurable Delimiter**: Customize field separators using short (`-d`) and long (`--delimiter`) flags, supporting standard and backslash-escaped control characters (e.g., `\t`).
- **Hierarchical Flattening**: Automatically flatten deeply nested JSON structures using clear dot notation namespaces.
- **Input Validation**: Ensure robust execution using strict type checks, format verification, and helpful error mapping without dumping stack traces.

## Tech Stack
- Runtime: Python 3.12
- Standard Library Modules: `json`, `csv`, `argparse`, `sys`, `os`

## Getting Started

### Prerequisites
- Python 3.12 or higher.

### Installation & Build
```sh
pip install -r requirements.txt 2>/dev/null || true
python -m compileall -q .
```

## Usage
```sh
python -m json2csv.main input.json output.csv -d ","
```

## Running Tests
```sh
python -m pytest
```

## License
MIT &copy; 2026 JSON-to-CSV CLI Contributors
