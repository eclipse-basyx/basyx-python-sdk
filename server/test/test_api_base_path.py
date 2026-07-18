# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import pathlib
import re
import unittest

SERVER_ROOT = pathlib.Path(__file__).resolve().parent.parent

API_PATH_REGEX = re.compile(r"/api/v[\d.]+")

FILES_TO_CHECK = [
    # Server routes
    SERVER_ROOT / "app" / "interfaces" / "discovery.py",
    SERVER_ROOT / "app" / "interfaces" / "registry.py",
    SERVER_ROOT / "app" / "interfaces" / "repository.py",
    # Dockerfiles
    SERVER_ROOT / "docker" / "discovery" / "Dockerfile",
    SERVER_ROOT / "docker" / "registry" / "Dockerfile",
    SERVER_ROOT / "docker" / "repository" / "Dockerfile",
    # Tests
    SERVER_ROOT / "test" / "interfaces" / "test_shells_asset_ids.py",
]


def _extract(path: pathlib.Path) -> str:
    match = API_PATH_REGEX.search(path.read_text())
    if match is None:
        raise AssertionError(str(path.relative_to(SERVER_ROOT)) + ": no base path found")
    return match.group(0)


def _list_divergences(values) -> str:
    output = "API base path diverges across files:\n"
    for p, v in values.items():
        output += f"\n{p} {v}"
    return output


class APIBasePathConsistencyTest(unittest.TestCase):
    def test_base_path_aligned_across_known_files(self) -> None:
        values = {}
        for path in FILES_TO_CHECK:
            values[str(path.relative_to(SERVER_ROOT))] = _extract(path)

        distinct = set(values.values())
        self.assertEqual(1, len(distinct), _list_divergences(values))
