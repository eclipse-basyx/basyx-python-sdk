# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

"""
This helper script checks if the Python versions defined in a `pyproject.toml` or `Dockerfile` coincide with the given
`min_version` and `max_version` and returns an error if they don't.
"""
import argparse
import re
import sys

from packaging.version import InvalidVersion, Version


def get_version_pyproject(file_path: str) -> str:
    with open(file_path, "r") as f:
        pyproject_content = f.read()

    match = re.search(r'requires-python\s*=\s*">=([\d.]+)"', pyproject_content)
    if not match:
        print(f"Error: `requires-python` field not found or invalid format in `{file_path}`")
        sys.exit(1)

    return match.group(1)

def get_version_dockerfile(file_path: str) -> str:
    with open(file_path, "r") as f:
        pyproject_content = f.read()

    match = re.search(r'^FROM\s+python:([\d.]+)', pyproject_content, re.MULTILINE)
    if not match:
        print(f"Error: Definition of base image `FROM python:x.x` not found in `{file_path}`")
        sys.exit(1)

    return match.group(1)

def main(file_path: str, is_dockerfile: bool, min_version: str, max_version: str) -> None:
    # Load and check `requires-python` version from `pyproject.toml`
    try:
        if is_dockerfile:
            used_version = get_version_dockerfile(file_path)
        else:
            used_version = get_version_pyproject(file_path)

        if Version(used_version) < Version(min_version):
            print(f"Error: Python version in `{file_path}` ({used_version}) "
                  f"is smaller than `min_version` ({min_version}).")
            sys.exit(1)
        if Version(used_version) > Version(max_version):
            print(f"Error: Python version in `{file_path}` ({used_version}) "
                  f"is greater than `max_version` ({max_version}).")
            sys.exit(1)

    except FileNotFoundError:
        print(f"Error: File not found: `{file_path}`.")
        sys.exit(1)

    print(f"Success: Version in `{file_path}` ({used_version}) "
          f"matches expected versions ([{min_version} to {max_version}]).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check Python version support and alignment with pyproject.toml or Dockerfile.")
    parser.add_argument("file_path", help="Path to the `pyproject.toml` or `Dockerfile` file to check.")
    parser.add_argument("--docker", action="store_true",
                        help="Set, if checking a `Dockerfile`, otherwise `pyproject.toml` is assumed.")
    parser.add_argument("min_version", help="The minimum Python version.")
    parser.add_argument("max_version", help="The maximum Python version.")
    args = parser.parse_args()

    try:
        main(args.file_path, args.docker, args.min_version, args.max_version)
    except InvalidVersion:
        print("Error: Invalid version format provided.")
        sys.exit(1)
