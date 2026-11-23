#!/usr/bin/env python3
# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Small helper script to setup a blank CouchDB server with a test database and a test user (e.g. for use in CI)

This script uses the ``test/test_config.ini`` and ``test/test_config.default.ini`` files to setup the CouchDB server
the way the tests will expect it. The admin user and password used to do the setup may be configured via command line:

    setup_testdb.py -u admin -p admin_password

If no CouchDB server is reachable at the configured URL, or the test database already exists, the script exits with
exit code 1, so that CI fails fast if the CouchDB service container isn't healthy. With ``--failsafe``, it exits with
exit code 0 in both cases instead.

In both cases, the script exits before it creates the test user and adds it to the ``_security`` object of the test
database. If an earlier run created the database but not the user, the tests cannot log in (``401``): they are
skipped, or fail if ``REQUIRE_COUCHDB_INTEGRATION_TESTS`` is set. To set up the server again, delete both the test
database and the test user; the script fails if the user already exists.
"""

import argparse
import base64
import configparser
import http.client
import json
import os.path
import sys
import urllib.error
import urllib.request

# Parse test config (required to setup the CouchDB as expected)
TEST_CONFIG = configparser.ConfigParser()
TEST_CONFIG.read(
    (
        os.path.join(os.path.dirname(__file__), "..", "test_config.default.ini"),
        os.path.join(os.path.dirname(__file__), "..", "test_config.ini"),
    )
)

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Setup CouchDB test database according to test_config.ini"
)
parser.add_argument("--admin-user", "-u", help="Name of the CouchDB admin user")
parser.add_argument(
    "--admin-password", "-p", help="Password of the CouchDB admin user", default=""
)
parser.add_argument(
    "--failsafe",
    "-f",
    action="store_true",
    help="Exit with exit code 0 even if no database server could be reached or the database already "
    "exists on the server.",
)
args = parser.parse_args()


# Some basic data for couchdb setup
default_headers = {
    "Accept": "application/json",
}
if args.admin_user is not None:
    default_headers["Authorization"] = "Basic %s" % base64.b64encode(
        ("%s:%s" % (args.admin_user, args.admin_password)).encode("ascii")
    ).decode("ascii")


# Check if CouchDB server is available
request = urllib.request.Request(
    TEST_CONFIG["couchdb"]["url"], headers=default_headers, method="HEAD"
)
try:
    urllib.request.urlopen(request, timeout=5)
except (OSError, http.client.HTTPException) as e:
    print(
        "Could not reach CouchDB server at {}: {}".format(
            TEST_CONFIG["couchdb"]["url"], e
        )
    )
    sys.exit(0 if args.failsafe else 1)

# The actual work
# Check if the System databases exist and create them otherwise
request = urllib.request.Request(
    "{}/_users".format(TEST_CONFIG["couchdb"]["url"]),
    headers=default_headers,
    method="HEAD",
)
try:
    urllib.request.urlopen(request, timeout=5)
except urllib.error.HTTPError as e:
    if e.code != 404:
        raise
    for db in ("_global_changes", "_replicator", "_users"):
        request = urllib.request.Request(
            "{}/{}".format(TEST_CONFIG["couchdb"]["url"], db),
            headers=default_headers,
            method="PUT",
        )
        urllib.request.urlopen(request, timeout=5)


# Create the database if not existing
request = urllib.request.Request(
    "{}/{}".format(TEST_CONFIG["couchdb"]["url"], TEST_CONFIG["couchdb"]["database"]),
    headers=default_headers,
    method="PUT",
)
try:
    urllib.request.urlopen(request, timeout=5)
except urllib.error.HTTPError as e:
    if e.code == 412:
        # TODO make more failsafe: Delete and recreate database if it exists already
        print(
            "CouchDB database {} already existed. Exiting ...".format(
                TEST_CONFIG["couchdb"]["database"]
            )
        )
        sys.exit(0 if args.failsafe else 1)
    else:
        raise


# Create the user if not existing
request = urllib.request.Request(
    "{}/_users/org.couchdb.user:{}".format(
        TEST_CONFIG["couchdb"]["url"], TEST_CONFIG["couchdb"]["user"]
    ),
    headers=default_headers,
    method="PUT",
    data=json.dumps(
        {
            "name": TEST_CONFIG["couchdb"]["user"],
            "password": TEST_CONFIG["couchdb"]["password"],
            "roles": [],
            "type": "user",
        }
    ).encode(),
)
# TODO make more failsafe: Set password of user if they exist already
urllib.request.urlopen(request, timeout=5)


# Add user as member of database
# TODO make more failsafe: Keep existing authorizations
request = urllib.request.Request(
    "{}/{}/_security".format(
        TEST_CONFIG["couchdb"]["url"], TEST_CONFIG["couchdb"]["database"]
    ),
    headers=default_headers,
    method="PUT",
    data=json.dumps(
        {
            "admins": {"names": [], "roles": []},
            "members": {"names": [TEST_CONFIG["couchdb"]["user"]], "roles": []},
        }
    ).encode(),
)
urllib.request.urlopen(request, timeout=5)
