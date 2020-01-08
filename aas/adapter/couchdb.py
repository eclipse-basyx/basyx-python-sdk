import abc
import http.client
import http.cookiejar
import json
from typing import Iterator, Dict, Optional, Any
import urllib.parse
import urllib.request
import urllib.error

from aas import model
from aas.adapter.json import json_serialization, json_deserialization


class CouchDBDatabase(model.AbstractObjectStore):
    def __init__(self, url: str, database: str):
        self.url = url
        self.database_name = database

        # Build custom URLlib OpenerDirector for persistent auth cookie handling
        # TODO make CouchDBDatabase thread safe by using one _opener per thread, with a shared cookielib.CookieJar
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    # TODO method to clear database
    # TODO method to delete database

    def login(self, user: str, password: str):
        request = urllib.request.Request(
            "{}/_session".format(self.url),
            headers={'Content-type': 'application/json'},
            method='POST',
            data=json.dumps({'name': user, 'password': password}).encode())
        self._do_request(request)

    def logout(self):
        request = urllib.request.Request(
            "{}/_session".format(self.url),
            headers={'Content-type': 'application/json'},
            method='DELETE')
        self._do_request(request)

    def check_database(self, create=False):
        """
        Check if the database exists and created it if not (and requested to do so)
        """
        request = urllib.request.Request(
            "{}/{}".format(self.url, self.database_name),
            headers={'Accept': 'application/json'},
            method='HEAD')
        try:
            self._do_request(request)
        except urllib.error.HTTPError as e:
            # If a HTTPError is raised, re-raise it, unless it is a 404 error and we are requested to create the
            # database
            if e.code != 400 or not create:
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

    def get_identifiable(self, identifier: model.Identifier) -> "CouchDBIdentifiable":
        """

        :param identifier:
        :return:
        :raises urllib.error.URLError: When encountering HTTP errors (see
                                       http://docs.couchdb.org/en/stable/api/basics.html#http-status-codes for a CouchDB
                                       error code reference)
        """
        # Create and issue HTTP request (raises HTTPError on status != 200)
        request = urllib.request.Request(
            "{}/{}/{}".format(self.url, self.database_name, self._transform_id(identifier)),
            headers={'Accept': 'application/json'})
        data = self._do_request(request)

        # Add CouchDB meta data (for later commits) to object
        obj = data['data']
        assert(isinstance(obj, CouchDBIdentifiable))  # TODO better error handling
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
        self._do_request(request)

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

    def discard(self, x: "CouchDBIdentifiable") -> None:
        # TODO allow x to be an Identifiable (retrieve revision from CouchDB in that case)
        request = urllib.request.Request(
            "{}/{}/{}?rev={}".format(self.url, self.database_name, self._transform_id(x.identification),
                                     x.couchdb_revision),
            headers={'Content-type': 'application/json'},
            method='DELETE')
        self._do_request(request)

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
        except urllib.error.HTTPError as e:
            if e.code == 400:
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
        # TODO
        return iter(())

    def _do_request(self, request: urllib.request.Request) -> Dict[str, Any]:
        """
        Perform a HTTP request to the CouchDB server

        This function performs the request, checks the response and does all the error handling and parsing of resulting
        JSON. It returns the retrieved document as Python dict or raises an Exception.
        """
        response = self._opener.open(request)
        # TODO better error handling (using "error" and "reason" from CouchDB response)

        # Check response & parse data to update couchdb_revision
        assert (isinstance(response, http.client.HTTPResponse))
        if request.get_method() == 'HEAD':
            return {}
        if response.getheader('Content-type') != 'application/json':
            raise ValueError("Unexpected Content-type header")
        data = json.load(response, cls=CouchDBJSONDecoder)
        assert(isinstance(data, dict))  # TODO better error handling
        return data

    @staticmethod
    def _transform_id(identifier: model.Identifier) -> str:
        return urllib.parse.quote("{}-{}".format(identifier.id_type.name, identifier.id), safe='')


class CouchDBIdentifiable(model.Identifiable, metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        super().__init__()
        self._store: Optional[CouchDBDatabase] = None
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
