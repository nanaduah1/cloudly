import json
from cloudly.http import HttpApi, Request


def test_middleware_request_is_called():
    class AuthMiddleware:
        def request(self, request: Request):
            request.set("auth", True)

    class MiddlewareApi(HttpApi):
        middleware = [AuthMiddleware]

        def get(self, request):
            return {"auth": request.auth}

    tested = MiddlewareApi()
    response = tested({"httpMethod": "GET"}, {})
    data = json.loads(response["body"])
    assert data["auth"] is True
