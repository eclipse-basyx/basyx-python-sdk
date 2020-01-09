# Copyright 2019 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

# TODO docstring

import abc
import http.client
import http.cookiejar
import json
from typing import Iterator, Dict, Optional, Any, Iterable, Union
import urllib.parse
import urllib.request
import urllib.error
import threading

from aas import model
from aas.adapter.json import json_serialization, json_deserialization


class CouchDBObjectStore(model.AbstractObjectStore):
    """
    An ObjectStore implementation for Identifiable PyI40AAS objects backed by a CouchDB database server.

    This ObjectStore stores each Identifiable object as a single JSON document in the configured CouchDB database. Each
    document's id is build from the object's identifier using the pattern {idtype}-{idvalue}; the document's contents
    comprise a single property "data", containing the JSON serialization of the PyI4.0AAS object. The aas.adapter.json
    package is used for serialization and deserialization of objects.

    Objects retrieved from the CouchDBObjectStore are instances of the appropriate PyI4.0AAS model class. Additionally,
    they inherit from the special base class `CouchDBIdentifiable`. It provides a `commit()` method to write back
    changes, which have been made to the object, to the database.

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
        self.url = url
        self.database_name = database

        # Build shared cookie jar for session caching and thread-local store for OpenerDirector
        self._cookie_jar = http.cookiejar.CookieJar()
        self._thread_local = threading.local()

    # TODO method to delete database
    # TODO add logging

    def login(self, user: str, password: str):
        """
        Login at the CouchDB server with the given user credentials.

        This method uses the /_session endpoint of the CouchDB server to obtain a session cookie, which is used for
        further HTTP requests. This is required
        """
        request = urllib.request.Request(
            "{}/_session".format(self.url),
            headers={'Content-type': 'application/json'},
            method='POST',
            data=json.dumps({'name': user, 'password': password}).encode())
        self._do_request(request)

    def logout(self):
        """
        Logout from the CouchDB server.

        This method uses the /_session endpoint of the CouchDB server to obtain a session cookie, which is used for
        further HTTP requests. This is required
        """
        request = urllib.request.Request(
            "{}/_session".format(self.url),
            headers={'Content-type': 'application/json'},
            method='DELETE')
        self._do_request(request)

    def check_database(self, create=False):
        """
        Check if the database exists and created it if not (and requested to do so)

        :param create: If True and the database does not exist, try to create it
        """
        request = urllib.request.Request(
            "{}/{}".format(self.url, self.database_name),
            headers={'Accept': 'application/json'},
            method='HEAD')
        try:
            self._do_request(request)
        except CouchDBServerError as e:
            # If an HTTPError is raised, re-raise it, unless it is a 404 error and we are requested to create the
            # database
            if e.code != 404 or not create:
                raise e
        else:
            # If no exception is given raised, the database is okay
            return

        # Create database
        request = urllib.request.Request(
            "{}/{}".format(self.url, self.database_name),
            headers={'Accept': 'application/json'},
            method='PUT')
        self._do_request(request)

    def get_identifiable(self, identifier: Union[str, model.Identifier]) -> "CouchDBIdentifiable":
        if isinstance(identifier, model.Identifier):
            identifier = self._transform_id(identifier, False)

        # Create and issue HTTP request (raises HTTPError on status != 200)
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, urllib.parse.quote(identifier, safe='')),
            headers={'Accept': 'application/json'})
        try:
            data = self._do_request(request)
        except CouchDBServerError as e:
            if e.code == 404:
                raise KeyError("No Identifiable with id {} found in CouchDB database".format(identifier)) from e
            raise

        # Add CouchDB meta data (for later commits) to object
        obj = data['data']
        if not isinstance(obj, CouchDBIdentifiable):
            raise CouchDBResponseError("The CouchDB document with id {} does not contain an identifiable AAS object."
                                       .format(identifier))
        obj._store = self
        obj.couchdb_revision = data['_rev']
        return obj

    def add(self, x: model.Identifiable) -> None:
        # Serialize data
        data = json.dumps({'data': x}, cls=json_serialization.AASToJsonEncoder)

        # Create and issue HTTP request (raises HTTPError on status != 200)
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, self._transform_id(x.identification)),
            headers={'Content-type': 'application/json'},
            method='PUT',
            data=data.encode())
        try:
            self._do_request(request)
        except CouchDBServerError as e:
            if e.code == 409:
                raise KeyError("Identifiable with id {} already exists in CouchDB database".format(x.identification))\
                    from e
            raise

    def commit(self, x: "CouchDBIdentifiable") -> None:
        # Serialize data
        data = json.dumps({'data': x, '_rev': x.couchdb_revision}, cls=json_serialization.AASToJsonEncoder)

        # Create and issue HTTP request (raises HTTPError on status != 200)
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, self._transform_id(x.identification)),
            headers={'Content-type': 'application/json'},
            method='PUT',
            data=data.encode())
        response_data = self._do_request(request)
        x.couchdb_revision = response_data['rev']
        # TODO handle ConflictErrors (HTTP 409)

    def discard(self, x: model.Identifiable) -> None:
        # If x is not a CouchDBIdentifiable, retrieve x from the database to get the current couchdb_revision
        if hasattr(x, 'couchdb_revision'):
            rev = x.couchdb_revision  # type: ignore
        else:
            current = self.get_identifiable(x.identification)
            # TODO handle KeyErrors (HTTP 404)
            rev = current.couchdb_revision

        request = urllib.request.Request(
            "{}/{}/{}?rev={}".format(self.url, self.database_name, self._transform_id(x.identification), rev),
            headers={'Content-type': 'application/json'},
            method='DELETE')
        self._do_request(request)
        # TODO handle KeyErrors (HTTP 404)

    def __contains__(self, x: object) -> bool:
        if isinstance(x, model.Identifier):
            identifier = x
        elif isinstance(x, model.Identifiable):
            identifier = x.identification
        else:
            return False
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, self._transform_id(identifier)),
            headers={'Accept': 'application/json'},
            method='HEAD')
        try:
            self._do_request(request)
        except CouchDBServerError as e:
            if e.code == 404:
                return False
            raise
        return True

    def __len__(self) -> int:
        request = urllib.request.Request(
            "{}/{}".format(self.url, self.database_name),
            headers={'Accept': 'application/json'})
        data = self._do_request(request)
        return data['doc_count']

    def __iter__(self) -> Iterator[model.Identifiable]:
        """
        Iterate all Identifiables in the CouchDB database.

        This method returns a lazy iterator, containing only a list of all identifiers in the database and retrieving
        the identifiable objects on the fly.
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
        request = urllib.request.Request(
            "{}/{}/_all_docs".format(self.url, self.database_name),
            headers={'Accept': 'application/json'})
        data = self._do_request(request)
        return CouchDBIdentifiableIterator(self, (row['id'] for row in data['rows']))

    def _do_request(self, request: urllib.request.Request) -> Dict[str, Any]:
        """
        Perform an HTTP request to the CouchDB server

        This function performs the request described by the given Request object, checks the response status code and
        either raises a CouchDBError or returns the parsed JSON response data.
        """
        # Create thread-local OpenerDirector with shared cookie jar if not existing in this thread
        if hasattr(self._thread_local, 'opener'):
            opener = self._thread_local.opener
        else:
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cookie_jar))
            self._thread_local.opener = opener

        # Do request and handle HTTP Errors
        try:
            response = opener.open(request)
        except urllib.error.HTTPError as e:
            if e.headers['Content-type'] != 'application/json':
                raise CouchDBResponseError("Unexpected Content-type header of response from {}"
                                           .format(request.full_url))

            if request.get_method() == 'HEAD':
                raise CouchDBServerError(e.code, "", "", "HTTP {}") from e

            try:
                data = json.load(e)
            except json.JSONDecodeError:
                raise CouchDBResponseError("Could not parse error message of HTTP {} response from {}"
                                           .format(e.code, request.full_url))
            raise CouchDBServerError(e.code, data['error'], data['reason'],
                                     "HTTP {}: {} (reason: {})".format(e.code, data['error'], data['reason'])) from e

        # Check response & parse data
        assert (isinstance(response, http.client.HTTPResponse))
        if request.get_method() == 'HEAD':
            return {}

        if response.getheader('Content-type') != 'application/json':
            raise CouchDBResponseError("Unexpected Content-type header")
        try:
            data = json.load(response, cls=CouchDBJSONDecoder)
        except json.JSONDecodeError as e:
            raise CouchDBResponseError("Could not parse CouchDB server response as JSON data.") from e
        return data

    @staticmethod
    def _transform_id(identifier: model.Identifier, url_quote=True) -> str:
        result = "{}-{}".format(identifier.id_type.name, identifier.id)
        if url_quote:
            result = urllib.parse.quote(result, safe='')
        return result


# TODO heading


class CouchDBIdentifiable(model.Identifiable, metaclass=abc.ABCMeta):
    # TODO docstring

    def __init__(self) -> None:
        super().__init__()
        self._store: Optional[CouchDBObjectStore] = None
        self.couchdb_revision: Optional[str] = None

    def commit_changes(self) -> None:
        if not self._store:
            raise RuntimeError("CouchDBIdentifiable is not associated with a store")
        self._store.commit(self)


class CouchDBAssetAdministrationShell(model.AssetAdministrationShell, CouchDBIdentifiable):
    pass


class CouchDBAsset(model.Asset, CouchDBIdentifiable):
    pass


class CouchDBConceptDescription(model.ConceptDescription, CouchDBIdentifiable):
    pass


class CouchDBSubmodel(model.Submodel, CouchDBIdentifiable):
    pass


class CouchDBJSONDecoder(json_deserialization.StrictAASFromJsonDecoder):
    # TODO docstring
    @classmethod
    def _construct_asset_administration_shell(
            cls, dct: Dict[str, object], object_class=model.AssetAdministrationShell) -> model.AssetAdministrationShell:
        return super()._construct_asset_administration_shell(dct, object_class=CouchDBAssetAdministrationShell)

    @classmethod
    def _construct_asset(cls, dct: Dict[str, object], object_class=model.Asset) -> model.Asset:
        return super()._construct_asset(dct, object_class=CouchDBAsset)

    @classmethod
    def _construct_concept_description(cls, dct: Dict[str, object], object_class=model.ConceptDescription)\
            -> model.ConceptDescription:
        return super()._construct_concept_description(dct, object_class=CouchDBConceptDescription)

    @classmethod
    def _construct_submodel(cls, dct: Dict[str, object], object_class=model.Submodel) -> model.Submodel:
        return super()._construct_submodel(dct, object_class=CouchDBSubmodel)


# TODO heading


class CouchDBError(Exception):
    """Base class of all exceptions raised by the CouchDBObjectStore"""
    pass


class CouchDBConnectionError(CouchDBError):
    """Exception raised by the CouchDBObjectStore when the CouchDB server could not be reached"""
    pass


class CouchDBResponseError(CouchDBError):
    """Exception raised by the CouchDBObjectStore when an HTTP of the CouchDB server could not be handled (e.g.
    no JSON body)"""
    pass


class CouchDBServerError(CouchDBError):
    """Exception raised by the CouchDBObjectStore when the CouchDB server returns an unexpected error code"""
    def __init__(self, code: int, error: str, reason: str, *args):
        super().__init__(*args)
        self.code = code
        self.error = error
        self.reason = reason
