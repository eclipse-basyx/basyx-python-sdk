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
"""
CouchDB backend for persistently storing AAS objects

This module provides the `CouchDBObjectStore` class, that implements the AbstractObjectStore interface for storing and
retrieving Identifiable PyI40AAS objects in/from a CouchDB server. The objects are serialized to JSON using the
aas.adapter.json package and transferred to the configured CouchDB database.

Typical usage:

    database = CouchDBObjectStore('localhost:5984', 'aas_test')
    database.login('user', 'password')

    submodel = aas.model.Submodel(...)
    database.add(submodel)

    aas = database.get_identifiable(aas.model.Identifier('https://acplt.org/MyAAS', aas.model.IdentifierType.IRI))
    aas.description['de'] = "Eine neue Beschreibung"
    aas.commit_changes()

    database.logout()

To allow committing changes, the objects retrieved from the CouchDBObjectStore are instances of special classes
(`CouchDBAssetAdministrationShell`, etc.), inheriting from the special base class `CouchDBIdentifiable`. However, these
classes also inherit from the appropriate class in `aas.model` to be used as any other PyI40AAS object.

Additionally, this module defines a custom Exception class `CouchDBError` and some subclasses. These Exceptions are used
to unambiguously report errors (connection errors, parser errors or HTTP errors from the server) when interacting with
the CouchDB server.
"""

import abc
import http.client
import http.cookiejar
import json
from typing import Iterator, Dict, Optional, Any, Iterable, Union
import urllib.parse
import urllib.request
import urllib.error
import threading
import logging

from .. import model
from .json import json_serialization, json_deserialization

logger = logging.getLogger(__name__)


class CouchDBObjectStore(model.AbstractObjectStore):
    """
    An ObjectStore implementation for Identifiable PyI40AAS objects backed by a CouchDB database server.

    This ObjectStore stores each Identifiable object as a single JSON document in the configured CouchDB database. Each
    document's id is build from the object's identifier using the pattern {idtype}-{idvalue}; the document's contents
    comprise a single property "data", containing the JSON serialization of the PyI40AAS object. The aas.adapter.json
    package is used for serialization and deserialization of objects.

    Objects retrieved from the CouchDBObjectStore are instances of the appropriate PyI40AAS model class. Additionally,
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

    def login(self, user: str, password: str):
        """
        Login at the CouchDB server with the given user credentials.

        This method uses the /_session endpoint of the CouchDB server to obtain a session cookie, which is used for
        further HTTP requests. This is required to be performed before any other request to the object store, unless
        the CouchDB server does not require authentication.

        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        logger.info("Logging in to CouchDB server %s with user %s ...", self.url, user)
        request = urllib.request.Request(
            "{}/_session".format(self.url),
            headers={'Content-type': 'application/json'},
            method='POST',
            data=json.dumps({'name': user, 'password': password}).encode())
        self._do_request(request)

    def logout(self):
        """
        Logout from the CouchDB server.

        This method uses the /_session endpoint of the CouchDB server to invalidate the user session and delete the
        session cookie.

        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        logger.info("Logging out from CouchDB server %s ...", self.url)
        request = urllib.request.Request(
            "{}/_session".format(self.url),
            headers={'Content-type': 'application/json'},
            method='DELETE')
        self._do_request(request)

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
        logger.info("Creating CouchDB database %s/%s ...", self.url, self.database_name)
        request = urllib.request.Request(
            "{}/{}".format(self.url, self.database_name),
            headers={'Accept': 'application/json'},
            method='PUT')
        self._do_request(request)

    def get_identifiable(self, identifier: Union[str, model.Identifier]) -> "CouchDBIdentifiable":
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
            self._do_request(request)
        except CouchDBServerError as e:
            if e.code == 409:
                raise KeyError("Identifiable with id {} already exists in CouchDB database".format(x.identification))\
                    from e
            raise

    def commit(self, x: "CouchDBIdentifiable") -> None:
        """
        Commit in-memory changes in a CouchDBIdentifiable PyI40AAS object to the database

        :param x: The changed object
        :raises KeyError: If the object does not exist in the database
        :raises CouchDBConflictError: If a concurrent modification (or deletion) in the database was detected
        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        logger.debug("Committing changes of object %s based on revision %s to CouchDB database ...",
                     repr(x), x.couchdb_revision)
        # Serialize data
        data = json.dumps({'data': x, '_rev': x.couchdb_revision}, cls=json_serialization.AASToJsonEncoder)

        # Create and issue HTTP request (raises HTTPError on status != 200)
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, self._transform_id(x.identification)),
            headers={'Content-type': 'application/json'},
            method='PUT',
            data=data.encode())
        try:
            response_data = self._do_request(request)
        except CouchDBServerError as e:
            if e.code == 409:
                raise CouchDBConflictError("Could not commit changes to id {} due to a concurrent modification in the "
                                           "database.".format(x.identification)) from e
            elif e.code == 404:
                raise KeyError("Object with id {} was not found in the database {}"
                               .format(x.identification, self.database_name)) from e
            raise
        x.couchdb_revision = response_data['rev']

    def discard(self, x: model.Identifiable, safe_delete=False) -> None:
        """
        Delete an Identifiable AAS object from the CouchDB database

        :param x: The object to be deleted
        :param safe_delete: If True, only delete the object if it has not been modified in the database in comparison to
                            the provided revision. This uses the CouchDB revision token and thus only works with
                            CouchDBIdentifiable objects retrieved from this database.
        :raises KeyError: If the object does not exist in the database
        :raises CouchDBConflictError: If safe_delete is true and the object has been modified or deleted in the database
        :raises CouchDBError: If error occur during the request to the CouchDB server (see `_do_request()` for details)
        """
        logger.debug("Deleting object %s from CouchDB database ...", repr(x))
        # If x is not a CouchDBIdentifiable, retrieve x from the database to get the current couchdb_revision
        if hasattr(x, 'couchdb_revision') and safe_delete:
            rev = x.couchdb_revision  # type: ignore
            logger.debug("using the object's stored revision token %s for deletion.",
                         x.couchdb_revision)  # type: ignore
        else:
            try:
                logger.debug("fetching the current object revision for deletion ...")
                current = self.get_identifiable(x.identification)
            except KeyError as e:
                raise KeyError("No AAS object with id {} exists in CouchDB database".format(x.identification)) from e
            rev = current.couchdb_revision
            logger.debug("using the current object revision %s for deletion.")

        request = urllib.request.Request(
            "{}/{}/{}?rev={}".format(self.url, self.database_name, self._transform_id(x.identification), rev),
            headers={'Content-type': 'application/json'},
            method='DELETE')
        try:
            self._do_request(request)
        except CouchDBServerError as e:
            if e.code == 404:
                raise KeyError("No AAS object with id {} exists in CouchDB database".format(x.identification)) from e
            elif e.code == 409:
                raise CouchDBConflictError(
                    "Object with id {} has been modified in the database since the version requested to be deleted."
                    .format(x.identification)) from e
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
            self._do_request(request)
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
        data = self._do_request(request)
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
        data = self._do_request(request)
        return CouchDBIdentifiableIterator(self, (row['id'] for row in data['rows']))

    def _do_request(self, request: urllib.request.Request) -> Dict[str, Any]:
        """
        Perform an HTTP request to the CouchDB server, parse the result and handle errors

        This function performs the request described by the given Request object, checks the response status code and
        either raises a CouchDBError or returns the parsed JSON response data.

        :raises CouchDBServerError: When receiving an HTTP status code != 200
        :raises CouchDBResponseError: When the HTTP response could not be parsed
        :raises CouchDBConnectionError: On errors while connecting to the CouchDB server
        """
        # Create thread-local OpenerDirector with shared cookie jar if not existing in this thread
        if hasattr(self._thread_local, 'opener'):
            opener = self._thread_local.opener
        else:
            logger.debug("Creating new urllib OpenerDirector for current thread.")
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cookie_jar))
            self._thread_local.opener = opener

        # Do request and handle HTTP Errors
        logger.debug("Sending HTTP request to CouchDB server: %s %s ...", request.get_method(), request.full_url)
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
            data = json.load(response, cls=CouchDBJSONDecoder)
        except json.JSONDecodeError as e:
            raise CouchDBResponseError("Could not parse CouchDB server response as JSON data.") from e
        return data

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


# #################################################################################################
# Special object classes for Identifiable PyI40AAS objects retrieved from the CouchDBObjectStore

class CouchDBIdentifiable(model.Identifiable, metaclass=abc.ABCMeta):
    """
    Special base class for Identifiable PyI40AAS retrieved from the CouchDBObjectStore, allowing to write back (commit)
    changes to the database.

    This is an abstract base class. For each Identifiable AAS object type, there is one subclass, inheriting from this
    abstract base class and the appropriate aas.model class.

    This base class provides the `commit_changes()` method and the `_store` and `couchdb_revision` attributes required
    to perform the commit action. `_store` holds a reference to the CouchDBObjectStore instance; `couchdb_revision`
    contains the CouchDB document revision token of the latest object revision in the database. It is transferred to
    CouchDB when committing changes to check for editing conflicts.
    """

    def __init__(self) -> None:
        super().__init__()
        self._store: Optional[CouchDBObjectStore] = None
        self.couchdb_revision: Optional[str] = None

    def commit_changes(self) -> None:
        if self._store is None:
            raise ValueError("CouchDBIdentifiable is not associated with a store")
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
    """
    Special json.JSONDecoder class for deserializing AAS objects received from the CouchDB server

    This class inherits from StrictAASFromJsonDecoder to deserialize AAS JSON structures into the corresponding PyI40AAS
    object classes. However, it overrides the constructor methods of all Identifiable AAS objects to create instances of
    the `CouchDBIdentifiable` classes, defined above, instead of the usual aas.model classes.
    """
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


# #################################################################################################
# Custom Exception classes for reporting errors during interaction with the CouchDB server

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


class CouchDBConflictError(CouchDBError):
    """Exception raised by the CouchDBObjectStore when an object could not be committed due to an concurrent
    modification in the database"""
    pass
