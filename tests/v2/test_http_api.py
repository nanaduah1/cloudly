from cloudly.http import HttpApi


def test_that_request_is_routed_to_get():
    class GetApi(HttpApi):
        def get(self, request):
            return {"statusCode": 200}

    tested = GetApi()
    response = tested({"httpMethod": "GET"}, {})
    assert response["statusCode"] == 200


def test_that_request_is_routed_to_post():
    class PostApi(HttpApi):
        def post(self, request):
            return {"statusCode": 200}

    tested = PostApi()
    response = tested({"httpMethod": "POST"}, {})
    assert response["statusCode"] == 200


def test_that_request_is_routed_to_put():
    class PutApi(HttpApi):
        def put(self, request):
            return {"statusCode": 200}

    tested = PutApi()
    response = tested({"httpMethod": "PUT"}, {})
    assert response["statusCode"] == 200


def test_that_request_is_routed_to_patch():
    class PatchApi(HttpApi):
        def patch(self, request):
            return {"statusCode": 200}

    tested = PatchApi()
    response = tested({"httpMethod": "PATCH"}, {})
    assert response["statusCode"] == 200


def test_that_request_is_routed_to_delete():
    class DeleteApi(HttpApi):
        def delete(self, request):
            return {"statusCode": 200}

    tested = DeleteApi()
    response = tested({"httpMethod": "DELETE"}, {})
    assert response["statusCode"] == 200


def test_that_request_is_routed_to_options():
    class OptionsApi(HttpApi):
        def options(self, request):
            return {"statusCode": 200}

    tested = OptionsApi()
    response = tested({"httpMethod": "OPTIONS"}, {})
    assert response["statusCode"] == 200


def test_request_with_path_params():
    class GetApi(HttpApi):
        def get(self, request, id):
            return id

    tested = GetApi()
    response = tested({"httpMethod": "GET", "pathParameters": {"id": "123"}}, {})
    assert response["statusCode"] == 200
    assert response["body"] == "123"


def test_that_we_can_return_dict():
    class GetApi(HttpApi):
        def get(self, request):
            return {"name": "John"}

    tested = GetApi()
    response = tested({"httpMethod": "GET"}, {})
    assert response["statusCode"] == 200
    assert response["body"] == '{"name": "John"}'
    assert response["headers"]["Content-Type"] == "application/json"


def test_that_we_can_return_string():
    class GetApi(HttpApi):
        def get(self, request):
            return "Hello"

    tested = GetApi()
    response = tested({"httpMethod": "GET"}, {})
    assert response["statusCode"] == 200
    assert response["body"] == "Hello"
    assert response["headers"]["Content-Type"] == "text/plain"


def test_that_we_can_define_handler_with_arg_and_kwargs():
    class GetApi(HttpApi):
        def get(self, request, *args, **kwargs):
            id = kwargs["id"]
            return id

    tested = GetApi()
    response = tested({"httpMethod": "GET", "pathParameters": {"id": "123"}}, {})
    assert response["statusCode"] == 200
    assert response["body"] == "123"
    assert response["headers"]["Content-Type"] == "text/plain"


def test_that_handler_catches_unhandled_exceptions():
    class GetApi(HttpApi):
        def get(self, request):
            raise Exception("Something went wrong")

    tested = GetApi()
    response = tested({"httpMethod": "GET"}, {})
    assert response["statusCode"] == 500
    assert response["body"] == "Something went wrong"
    assert response["headers"]["Content-Type"] == "text/plain"


def test_that_handler_returns_not_implemented_error():
    class GetApi(HttpApi):
        pass

    tested = GetApi()
    response = tested({"httpMethod": "GET"}, {})
    assert response["statusCode"] == 501
    assert response["body"] == "Method not implemented"
    assert response["headers"]["Content-Type"] == "text/plain"
