import json
from typing import Any, Union
from cloudly.http.context import RequestContext
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


class Request(object):
    def __init__(self, data: dict):
        self._event_data = data
        self.context = RequestContext(data)

    @property
    def version(self):
        return self._event_data["version"]

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
        if hasattr(self, method):
            handler = getattr(self, method)

            # All arguments except self and request
            arg_names = handler.__code__.co_varnames
            constant_args = ("self", "request")
            handler_args = (a for a in arg_names if a not in constant_args)

            # Extract only the parameters the handler needs
            actual_args = {
                k: v for k, v in path_parameters.items() if k in handler_args
            }

            def _logexception(e):
                if self.logger:
                    self.logger.error(str(e))

            try:
                return handler(request, **actual_args)
            except HttpError as e:
                _logexception(e)
                return HttpErrorResponse(e).serialize()
            except Exception as e:
                _logexception(e)
                return HttpErrorResponse(HttpError(500, str(e))).serialize()
        else:
            error = HttpError(501, "Method not implemented")
            return HttpErrorResponse(error).serialize()


class ResponseMixin(object):
    def respond(
        self,
        response: Union[Response, dict, str, int, float, bool, bytes],
        status_code: int = 200,
        headers: dict = None,
    ):
        if isinstance(response, (Response, JsonResponse)):
            return response.serialize()
        elif isinstance(response, dict):
            return JsonResponse(
                data=response,
                status=status_code,
                headers=headers,
            ).serialize()
        elif isinstance(response, (str, bytes, int, float, bool)):
            return Response(
                data=response,
                status=status_code,
                headers=headers,
            ).serialize()
        else:
            raise ValueError(
                "Response must be instance of Response, dict or str, got {}".format(
                    type(response)
                )
            )


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
    logger: Logger = None

    def __call__(self, event: dict, context):
        return self.dispatch(event, context)
