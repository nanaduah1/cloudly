import json
from typing import Any, Union
from cloudly.http.context import RequestContext
from cloudly.http.exceptions import ValidationError
from cloudly.http.utils import DecimalEncoder
from cloudly.logging.logger import Logger


class HttpError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class Response(object):
    def __init__(self, data: str, status: int = 200, headers: dict = None):
        self._data = data
        self._status_code = status
        self._headers = headers or {}

    def serialize(self) -> dict:
        default_headers = {"Content-Type": "text/plain"}
        headers = {**default_headers, **self._headers}
        return {
            "statusCode": self._status_code,
            "headers": headers,
            "body": self._data,
        }


class JsonResponse(Response):
    def __init__(self, data: dict, status: int = 200, headers: dict = None):
        _headers = {"Content-Type": "application/json"}
        if headers:
            _headers.update(headers)
        super().__init__(json.dumps(data, cls=DecimalEncoder), status, _headers)


class HttpErrorResponse(Response):
    def __init__(self, error: HttpError):
        super().__init__({"error": str(error)}, error.status)


class User:
    def __init__(self, user: dict):
        custom_attributes = {
            k.split(":")[1]: v for k, v in user.items() if k.startswith("custom:")
        }
        self._user = user
        self.custom = type("CustomObj", (object,), custom_attributes)()

    def __getattr__(self, name):
        return self._user.get(name)


class Request(object):
    def __init__(self, data: dict):
        self._event_data = data
        self.context = RequestContext(data)
        self.user = None

    @property
    def version(self):
        return self._event_data.get("version")

    @property
    def headers(self):
        return self._event_data["headers"]

    @property
    def method(self):
        if self.version == "2.0":
            return self._event_data["requestContext"]["http"]["method"]
        else:
            return self._event_data["httpMethod"]

    def json(self) -> dict:
        return json.loads(self._event_data.get("body", "{}"))

    @property
    def pathParameters(self) -> dict:
        return self._event_data.get("pathParameters") or {}

    @property
    def query(self) -> dict:
        return self._event_data.get("queryStringParameters") or {}

    @property
    def host(self) -> str:
        return self.headers.get("Host", "")

    @property
    def body(self) -> str:
        return self._event_data.get("body", "")

    def set(self, key: str, value: Any):
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class RequestDispatcher(object):
    def dispatch(self, request: Request, context: Any):
        method = request.method.lower()
        path_parameters = request.pathParameters

        handler = getattr(self, method, None)
        if not handler:
            error = HttpError(501, "Method not implemented")
            return HttpErrorResponse(error).serialize()

        actual_args = {}
        if path_parameters:
            actual_args.update(path_parameters)

        try:
            response = handler(request, **actual_args)
            return self._respond(response)
        except HttpError as e:
            self._logexception(e)
            return HttpErrorResponse(e).serialize()
        except ValidationError as e:
            self._logexception(e)
            return HttpErrorResponse(HttpError(400, str(e))).serialize()
        except Exception as e:
            self._logexception(e)
            return HttpErrorResponse(HttpError(500, str(e))).serialize()

    def _logexception(self, e):
        if self.logger:
            self.logger.error(str(e))
        print(e)


class ResponseMixin(object):
    def _respond(
        self,
        response: Union[Response, dict, str, int, float, bool, bytes],
        status_code: int = 200,
        headers: dict = None,
    ):
        try:
            if isinstance(response, dict):
                response = JsonResponse(response, status_code, headers)
            elif isinstance(response, (str, int, float, bool, bytes)):
                response = Response(str(response), status_code, headers)
            elif isinstance(response, ValidationError):
                response = HttpErrorResponse(HttpError(400, str(response)))
            elif isinstance(response, HttpError):
                self._logexception(response)
                response = HttpErrorResponse(response)
            elif isinstance(response, Exception):
                self._logexception(response)
                response = HttpErrorResponse(HttpError(500, str(response)))
            return response.serialize()
        except Exception as e:
            print(e)
            self._logexception(e)
            return HttpErrorResponse(HttpError(500, str(e))).serialize()


class MiddlewareMixin(object):
    def __init__(self, *args, **kwargs):
        self.middleware = [cls() for cls in getattr(self, "middleware", [])]
        super().__init__(*args, **kwargs)

    def dispatch(self, event: dict, context: Any):
        request = Request(event)
        for middleware in self.middleware:
            if hasattr(middleware, "request"):
                middleware.request(request)
        return super().dispatch(request, context)


class HttpApi(MiddlewareMixin, RequestDispatcher, ResponseMixin):
    def __init__(self, logger: Logger = None):
        self.logger = logger
        super().__init__()

    def __call__(self, event: dict, context):
        return self.dispatch(event, context)
