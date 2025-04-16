import itertools
from typing import Iterable, Type, Iterator, Tuple

import werkzeug.exceptions
import werkzeug.routing
import werkzeug.utils
from werkzeug import Response, Request
from werkzeug.exceptions import NotFound, BadRequest
from werkzeug.routing import MapAdapter

from basyx.aas import model
from basyx.aas.model import AbstractObjectStore
from ..http_api_helpers import T
from server.app.response import get_response_type, http_exception_to_response


class BaseWSGIApp:
    url_map: werkzeug.routing.Map

    # TODO: the parameters can be typed via builtin wsgiref with Python 3.11+
    def __call__(self, environ, start_response) -> Iterable[bytes]:
        response: Response = self.handle_request(Request(environ))
        return response(environ, start_response)

    @classmethod
    def _get_slice(cls, request: Request, iterator: Iterable[T]) -> Tuple[Iterator[T], int]:
        limit_str = request.args.get('limit', default="10")
        cursor_str = request.args.get('cursor', default="0")
        try:
            limit, cursor = int(limit_str), int(cursor_str)
            if limit < 0 or cursor < 0:
                raise ValueError
        except ValueError:
            raise BadRequest("Cursor and limit must be positive integers!")
        start_index = cursor
        end_index = cursor + limit
        paginated_slice = itertools.islice(iterator, start_index, end_index)
        return paginated_slice, end_index

    def handle_request(self, request: Request):
        map_adapter: MapAdapter = self.url_map.bind_to_environ(request.environ)
        try:
            response_t = get_response_type(request)
        except werkzeug.exceptions.NotAcceptable as e:
            return e

        try:
            endpoint, values = map_adapter.match()
            return endpoint(request, values, response_t=response_t, map_adapter=map_adapter)

        # any raised error that leaves this function will cause a 500 internal server error
        # so catch raised http exceptions and return them
        except werkzeug.exceptions.HTTPException as e:
            return http_exception_to_response(e, response_t)


class ObjectStoreWSGIApp(BaseWSGIApp):
    object_store: AbstractObjectStore

    def _get_all_obj_of_type(self, type_: Type[model.provider._IT]) -> Iterator[model.provider._IT]:
        for obj in self.object_store:
            if isinstance(obj, type_):
                obj.update()
                yield obj

    def _get_obj_ts(self, identifier: model.Identifier, type_: Type[model.provider._IT]) -> model.provider._IT:
        identifiable = self.object_store.get(identifier)
        if not isinstance(identifiable, type_):
            raise NotFound(f"No {type_.__name__} with {identifier} found!")
        identifiable.update()
        return identifiable
