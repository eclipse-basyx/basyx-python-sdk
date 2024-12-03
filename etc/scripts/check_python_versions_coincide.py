"""
This helper script checks if the Python versions defined in a `pyproject.toml` coincide with the given `min_version`
and `max_version` and returns an error if they don't.
"""
import re
import argparse
import sys
from packaging.version import Version, InvalidVersion

def main(pyproject_toml_path: str, min_version: str, max_version: str) -> None:
    # Load and check `requires-python` version from `pyproject.toml`
    try:
        with open(pyproject_toml_path, "r") as f:
            pyproject_content = f.read()

        match = re.search(r'requires-python\s*=\s*">=([\d.]+)"', pyproject_content)
        if not match:
            print(f"Error: `requires-python` field not found or invalid format in `{pyproject_toml_path}`")
            sys.exit(1)

        pyproject_version = match.group(1)
        if Version(pyproject_version) < Version(min_version):
            print(f"Error: Python version in `{pyproject_toml_path}` `requires-python` ({pyproject_version}) "
                  f"is smaller than `min_version` ({min_version}).")
            sys.exit(1)

    except FileNotFoundError:
        print(f"Error: File not found: `{pyproject_toml_path}`.")
        sys.exit(1)

    print(f"Success: Version in pyproject.toml `requires-python` (>={pyproject_version}) "
          f"matches expected versions ([{min_version} to {max_version}]).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Python version support and alignment with pyproject.toml.")
    parser.add_argument("pyproject_toml_path", help="Path to the `pyproject.toml` file to check.")
    parser.add_argument("min_version", help="The minimum Python version.")
    parser.add_argument("max_version", help="The maximum Python version.")
    args = parser.parse_args()

    try:
        main(args.pyproject_toml_path, args.min_version, args.max_version)
    except InvalidVersion:
        print("Error: Invalid version format provided.")
        sys.exit(1)
