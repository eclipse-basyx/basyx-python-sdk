# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""
Todo: Add module docstring
"""
from typing import List, Dict, Any
import re
import urllib.parse
import urllib.request
import urllib.error
import logging
import json
import http.client

from . import backends
from aas.adapter.json import json_deserialization


logger = logging.getLogger(__name__)


class CouchDBBackend(backends.Backend):
    @classmethod
    def update_object(cls,
                      updated_object: "Referable",  # type: ignore
                      store_object: "Referable",  # type: ignore
                      relative_path: List[str]) -> None:
        url = CouchDBBackend._parse_source(store_object.source)
        request = urllib.request.Request(urllib.parse.quote(url, safe=""),
                                         headers={'Accept': 'application/json'})
        try:
            data = CouchDBBackend._do_request(request)
        except CouchDBServerError as e:
            if e.code == 404:
                raise KeyError("No Identifiable found in CouchDB at {}".format(url)) from e
            raise

        # Add CouchDB meta data (for later commits) to object
        store_obj = data['data']
        # if not isinstance(obj, "Referable"):  # todo
        #     raise CouchDBResponseError(
        #         "The CouchDB document with id {} does not contain an identifiable AAS object."
        #         .format(identifier))

    @classmethod
    def commit_object(cls,
                      committed_object: "Referable",  # type: ignore
                      store_object: "Referable",  # type: ignore
                      relative_path: List[str]) -> None:
        pass

    @classmethod
    def _parse_source(cls, source: str) -> str:
        """
        Parses the source parameter of a model.Referable object

        :param source: Source string of the model.Referable object
        :return: URL to the document
        :raises CouchDBBackendSourceError, if the source has the wrong format
        """
        url = ""
        couchdb_s = re.match("couchdbs:", source)  # Note: Works, since match only checks the beginning of the string
        if couchdb_s:
            url = source.replace("couchdbs:", "https://", 1)
        else:
            couchdb_wo_s = re.match("couchdb:", source)
            if couchdb_wo_s:
                url = source.replace("couchdb:", "http://", 1)
            else:
                raise CouchDBSourceError("Source has wrong format. "
                                         "Expected to start with {couchdb, couchdbs}, got {" + source + "}")
        return url

    @classmethod
    def _do_request(cls, request: urllib.request.Request) -> Dict[str, Any]:
        """
        Perform an HTTP request to the CouchDBServer, parse the result and handle errors

        :param request:
        :return:
        """
        opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(_credentials_store))
        try:
            response = opener.open(request)
        except urllib.error.HTTPError as e:
            logger.debug("Request %s %s finished with HTTP status code %s.",
                         request.get_method(), request.full_url, e.code)
            if e.headers.get('Content-type', None) != 'application/json':
                raise CouchDBResponseError("Unexpected Content-type header {} of response from CouchDB server"
                                           .format(e.headers.get('Content-type', None)))

            if request.get_method() == 'HEAD':
                raise CouchDBServerError(e.code, "", "", "HTTP {}") from e

            try:
                data = json.load(e)
            except json.JSONDecodeError:
                raise CouchDBResponseError("Could not parse error message of HTTP {}"
                                           .format(e.code))
            raise CouchDBServerError(e.code, data['error'], data['reason'],
                                     "HTTP {}: {} (reason: {})".format(e.code, data['error'], data['reason'])) from e
        except urllib.error.URLError as e:
            raise CouchDBConnectionError("Error while connecting to the CouchDB server: {}".format(e)) from e

        # Check response & parse data
        assert (isinstance(response, http.client.HTTPResponse))
        logger.debug("Request %s %s finished successfully.", request.get_method(), request.full_url)
        if request.get_method() == 'HEAD':
            return {}

        if response.getheader('Content-type') != 'application/json':
            raise CouchDBResponseError("Unexpected Content-type header")
        try:
            data = json.load(response, cls=json_deserialization.AASFromJsonDecoder)
        except json.JSONDecodeError as e:
            raise CouchDBResponseError("Could not parse CouchDB server response as JSON data.") from e
        return data


# Global registry for credentials for CouchDB Servers
_credentials_store: urllib.request.HTTPPasswordMgrWithDefaultRealm = urllib.request.HTTPPasswordMgrWithDefaultRealm()


def register_credentials(url: str, username: str, password: str):
    """
    Register the credentials of a CouchDB server to the global credentials store

    Todo: make thread safe

    :param url: Toplevel URL
    :param username: Username to that CouchDB instance
    :param password: Password to the Username
    """
    _credentials_store.add_password(None, url, username, password)


# #################################################################################################
# Custom Exception classes for reporting errors during interaction with the CouchDB server

class CouchDBError(Exception):
    pass


class CouchDBSourceError(CouchDBError):
    """Exception raised when the source has the wrong format"""
    pass


class CouchDBConnectionError(CouchDBError):
    """Exception raised when the CouchDB server could not be reached"""
    pass


class CouchDBResponseError(CouchDBError):
    """Exception raised by when an HTTP of the CouchDB server could not be handled (e.g.
    no JSON body)"""
    pass


class CouchDBServerError(CouchDBError):
    """Exception raised when the CouchDB server returns an unexpected error code"""
    def __init__(self, code: int, error: str, reason: str, *args):
        super().__init__(*args)
        self.code = code
        self.error = error
        self.reason = reason


class CouchDBConflictError(CouchDBError):
    """Exception raised when an object could not be committed due to an concurrent
    modification in the database"""
    pass
