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
from typing import List, Dict, Any, Optional, Iterator, Iterable
import re
import urllib.parse
import urllib.request
import urllib.error
import logging
import json
import http.client

from . import backends
from aas.adapter.json import json_deserialization, json_serialization
from aas import model


logger = logging.getLogger(__name__)


class CouchDBBackend(backends.Backend):
    """
    This Backend stores each Identifiable object as a single JSON document in the configured CouchDB database. Each
    document's id is build from the object's identifier using the pattern {idtype}-{idvalue}; the document's contents
    comprise a single property "data", containing the JSON serialization of the PyI40AAS object. The aas.adapter.json
    package is used for serialization and deserialization of objects.
    """
    @classmethod
    def update_object(cls,
                      updated_object: "Referable",  # type: ignore
                      store_object: "Referable",  # type: ignore
                      relative_path: List[str]) -> None:

        if not isinstance(store_object, model.Identifiable):
            raise CouchDBSourceError("The given store_object is not Identifiable, therefore cannot be found "
                                     "in the CouchDB")
        url = CouchDBBackend._parse_source(store_object.source)
        request = urllib.request.Request(url,
                                         headers={'Accept': 'application/json'})
        try:
            data = CouchDBBackend.do_request(request)
        except CouchDBServerError as e:
            if e.code == 404:
                raise KeyError("No Identifiable found in CouchDB at {}".format(url)) from e
            raise

        updated_store_object = data['data']
        store_object.update_from(updated_store_object)

    @classmethod
    def commit_object(cls,
                      committed_object: "Referable",  # type: ignore
                      store_object: "Referable",  # type: ignore
                      relative_path: List[str]) -> None:
        if not isinstance(store_object, model.Identifiable):
            raise CouchDBSourceError("The given store_object is not Identifiable, therefore cannot be found "
                                     "in the CouchDB")
        url = CouchDBBackend._parse_source(store_object.source)
        # We need to get the revision of the object, if it already exists, otherwise we cannot write to the Couchdb
        request = urllib.request.Request(
            url,
            headers={'Content-type': 'application/json'},
            method='GET'
        )
        couchdb_revision: Optional[str] = None
        try:
            revision_data = CouchDBBackend.do_request(request)
            couchdb_revision = revision_data['_rev']
        except CouchDBServerError as e:
            if not e.code == 404:
                raise

        data_to_commit: Dict[str, Any] = {'data': store_object}
        if couchdb_revision:
            data_to_commit['_rev'] = couchdb_revision
        data = json.dumps(data_to_commit, cls=json_serialization.AASToJsonEncoder)
        request = urllib.request.Request(
            url,
            headers={'Content-type': 'application/json'},
            method='PUT',
            data=data.encode())
        try:
            CouchDBBackend.do_request(request)
        except CouchDBServerError as e:
            if e.code == 409:
                raise CouchDBConflictError("Could not commit changes to id {} due to a concurrent modification in the "
                                           "database.".format(store_object.identification)) from e
            elif e.code == 404:
                raise KeyError("Object with id {} was not found in the CouchDB at {}"
                               .format(store_object.identification, url)) from e
            raise

    @classmethod
    def delete_object(cls, obj: "Referable"):  # type: ignore
        """
        Deletes the given object from the couchdb

        :param obj: Object to delete
        """
        if not isinstance(obj, model.Identifiable):
            raise CouchDBSourceError("The given store_object is not Identifiable, therefore cannot be found "
                                     "in the CouchDB")
        url = CouchDBBackend._parse_source(obj.source)
        # We need to get the revision of the object, if it already exists, otherwise we cannot write to the Couchdb
        req = urllib.request.Request(
            url,
            headers={'Content-type': 'application/json'},
            method='GET'
        )
        try:
            data = CouchDBBackend.do_request(req)
            couchdb_revision: str = data['_rev']
        except CouchDBServerError as e:
            if e.code == 404:
                raise KeyError("Object with id {} was not found in the CouchDB at {}"
                               .format(obj.identification, url)) from e
            raise

        req = urllib.request.Request(url+"?rev="+couchdb_revision,
                                     headers={'Content-type': 'application/json'},
                                     method='DELETE')
        try:
            CouchDBBackend.do_request(req)
        except CouchDBServerError as e:
            if e.code == 409:
                raise CouchDBConflictError("Could not delete object with to id {} due to a concurrent modification in "
                                           "the database.".format(obj.identification)) from e
            elif e.code == 404:
                raise KeyError("Object with id {} was not found in the CouchDB at {}"
                               .format(obj.identification, url)) from e
            raise

    @classmethod
    def _parse_source(cls, source: str) -> str:
        """
        Parses the source parameter of a model.Referable object

        :param source: Source string of the model.Referable object
        :return: URL to the document
        :raises CouchDBBackendSourceError, if the source has the wrong format
        """
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
    def do_request(cls, request: urllib.request.Request) -> Dict[str, Any]:
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
_credentials_store: urllib.request.HTTPPasswordMgrWithPriorAuth = urllib.request.HTTPPasswordMgrWithPriorAuth()
# todo: Why does this work and not HTTPPasswordMgrWithBasicAuth?
# https://stackoverflow.com/questions/29708708/http-basic-authentication-not-working-in-python-3-4


def register_credentials(url: str, username: str, password: str):
    """
    Register the credentials of a CouchDB server to the global credentials store

    Todo: make thread safe

    :param url: Toplevel URL
    :param username: Username to that CouchDB instance
    :param password: Password to the Username
    """
    _credentials_store.add_password(None, url, username, password, is_authenticated=True)


class CouchDBObjectStore(model.AbstractObjectStore):
    """
    An ObjectStore implementation for Identifiable PyI40AAS objects backed by a CouchDB database server.

    todo: adapt the following text
    All methods of the `CouchDBObjectStore` are blocking, i.e. they stop the current thread's execution until they
    receive a response from the CouchDB server (or encounter a timeout). However, the `CouchDBObjectStore` objects are
    thread-safe, meaning that you may run multiple method calls on the same CouchDBObjectStore in parallel in different
    threads. For example, you could use a ThreadPoolExecutor to add a large number of objects to the database:

        import concurrent.futures
        submodels = [submodel1, submodel2, submodel3]
        database = CouchDBObjectStore('localhost:5984', 'aas_test')
        database.login('test', 'test')
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.map(database.add, submodels)

    """
    def __init__(self, url: str, database: str):
        """
        Initializer of class CouchDBObjectStore

        :param url: URL to the CouchDB
        :param database: Name of the Database inside the CouchDB
        """
        self.url: str = url
        self.database_name: str = database
        self.ssl: bool = False
        if re.match("https:", self.url):
            self.ssl = True

    def check_database(self, create=False):
        """
        Check if the database exists and created it if not (and requested to do so)

        :param create: If True and the database does not exist, try to create it
        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        request = urllib.request.Request(
            "{}/{}".format(self.url, self.database_name),
            headers={'Accept': 'application/json'},
            method='HEAD')
        try:
            CouchDBBackend.do_request(request)
        except CouchDBServerError as e:
            # If an HTTPError is raised, re-raise it, unless it is a 404 error and we are requested to create the
            # database
            if e.code != 404 or not create:
                raise e
        else:
            # If no exception is given raised, the database is okay
            return

        # Create database
        logger.info("Creating CouchDB database %s/%s ...", self.url, self.database_name)
        request = urllib.request.Request(
            "{}/{}".format(self.url, self.database_name),
            headers={'Accept': 'application/json'},
            method='PUT')
        CouchDBBackend.do_request(request)

    def get_identifiable(self, identifier: model.Identifier) -> model.Identifiable:
        """
        Retrieve an AAS object from the CouchDB by its Identifier

        :raises KeyError: If no such object is stored in the database
        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        if isinstance(identifier, model.Identifier):
            identifier = self._transform_id(identifier, False)

        # Create and issue HTTP request (raises HTTPError on status != 200)
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, urllib.parse.quote(identifier, safe='')),
            headers={'Accept': 'application/json'})
        try:
            data = CouchDBBackend.do_request(request)
        except CouchDBServerError as e:
            if e.code == 404:
                raise KeyError("No Identifiable with id {} found in CouchDB database".format(identifier)) from e
            raise

        # Add CouchDB meta data (for later commits) to object
        obj = data['data']
        if not isinstance(obj, model.Identifiable):
            raise CouchDBResponseError("The CouchDB document with id {} does not contain an identifiable AAS object."
                                       .format(identifier))
        obj._store = self
        obj.couchdb_revision = data['_rev']
        return obj

    def add(self, x: model.Identifiable) -> None:
        """
        Add an object to the store

        :raises KeyError: If an object with the same id exists already in the database
        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        logger.debug("Adding object %s to CouchDB database ...", repr(x))
        # Serialize data
        data = json.dumps({'data': x}, cls=json_serialization.AASToJsonEncoder)

        # Create and issue HTTP request (raises HTTPError on status != 200)
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, self._transform_id(x.identification)),
            headers={'Content-type': 'application/json'},
            method='PUT',
            data=data.encode())
        try:
            CouchDBBackend.do_request(request)
        except CouchDBServerError as e:
            if e.code == 409:
                raise KeyError("Identifiable with id {} already exists in CouchDB database".format(x.identification))\
                    from e
            raise

    def __contains__(self, x: object) -> bool:
        """
        Check if an object with the given Identifier or the same Identifier as the given object is contained in the
        CouchDB database

        :param x: AAS object Identifier or Identifiable AAS object
        :return: True if such an object exists in the database, False otherwise
        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        if isinstance(x, model.Identifier):
            identifier = x
        elif isinstance(x, model.Identifiable):
            identifier = x.identification
        else:
            return False
        logger.debug("Checking existance of object with id %s in database ...", repr(x))
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, self._transform_id(identifier)),
            headers={'Accept': 'application/json'},
            method='HEAD')
        try:
            CouchDBBackend.do_request(request)
        except CouchDBServerError as e:
            if e.code == 404:
                return False
            raise
        return True

    def __len__(self) -> int:
        """
        Retrieve the number of objects in the CouchDB database

        :return: The number of objects (determined from the number of documents)
        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        logger.debug("Fetching number of documents from database ...")
        request = urllib.request.Request(
            "{}/{}".format(self.url, self.database_name),
            headers={'Accept': 'application/json'})
        data = CouchDBBackend.do_request(request)
        return data['doc_count']

    def __iter__(self) -> Iterator[model.Identifiable]:
        """
        Iterate all Identifiables in the CouchDB database.

        This method returns a lazy iterator, containing only a list of all identifiers in the database and retrieving
        the identifiable objects on the fly.

        :raises CouchDBError: If error occur during fetching the list of objects from the CouchDB server (see
                              `_do_request()` for details)
        """
        # Iterator class storing the list of ids and fetching Identifiable objects on the fly
        class CouchDBIdentifiableIterator(Iterator[model.Identifiable]):
            def __init__(self, store: CouchDBObjectStore, ids: Iterable[str]):
                self._iter = iter(ids)
                self._store = store

            def __next__(self):
                next_id = next(self._iter)
                return self._store.get_identifiable(next_id)

        # Fetch a list of all ids and construct Iterator object
        logger.debug("Creating iterator over objects in database ...")
        request = urllib.request.Request(
            "{}/{}/_all_docs".format(self.url, self.database_name),
            headers={'Accept': 'application/json'})
        data = CouchDBBackend.do_request(request)
        return CouchDBIdentifiableIterator(self, (row['id'] for row in data['rows']))

    @staticmethod
    def _transform_id(identifier: model.Identifier, url_quote=True) -> str:
        """
        Helper method to represent an ASS Identifier as a string to be used as CouchDB document id

        :param url_quote: If True, the result id string is url-encoded to be used in a HTTP request URL
        """
        result = "{}-{}".format(identifier.id_type.name, identifier.id)
        if url_quote:
            result = urllib.parse.quote(result, safe='')
        return result

    def generate_source(self, identifiable: model.Identifiable):
        """
        Generates the source string for an Identifiable object that is backed by the Couchdb

        :param identifiable: Identifiable object
        """
        source: str = self.url
        if self.ssl:
            source.replace("https://", "couchdbs:")
        else:
            source.replace("http://", "couchdb")
        source += self.database_name + "/" + self._transform_id(identifiable.identification)
        identifiable.source = source


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
