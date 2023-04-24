import json
from cloudly.http.request import http_api

from cloudly.http.validators import IntegerNumber, string_field
from flowfast.step import Task, Mapping

validation_schema = {
    "age": [
        IntegerNumber(
            "age",
            max=5,
            min=0,
        )
    ],
    "name": string_field("name", min=5, max=20, required=True),
}


def test_blank_api():
    @http_api()
    def handler(event, context):
        pass

    tested = handler
    response = tested({}, {})
    assert response["statusCode"] == 200


def test_validator_with_invalid_input():
    @http_api(validation_schema=validation_schema)
    def handler(event, context):
        pass

    tested = handler
    response = tested({}, {})
    assert response["statusCode"] == 400


def test_validator_with_valid_input():
    @http_api(validation_schema=validation_schema)
    def handler(event, context):
        pass

    tested = handler
    response = tested({"body": json.dumps({"name": "Yaw Baah", "age": 1})}, {})
    assert response["statusCode"] == 200


class AddHello(Task):
    def process(self, input: Mapping) -> Mapping:
        return {**input, "Hello": "World!"}


class AddYellow(Task):
    def process(self, input: Mapping) -> Mapping:
        return {**input, "Yellow": "World!"}


def test_http_api_with_hello_task():
    @http_api(AddHello())
    def handler(event, context):
        pass

    tested = handler
    response = tested({}, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["Hello"] == "World!"


def test_http_api_with_2_pipeline_tasks():
    @http_api(AddHello(), AddYellow())
    def handler(event, context):
        pass

    tested = handler
    response = tested({}, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["Hello"] == "World!"
    assert body["Yellow"] == "World!"


def test_http_api_with_custom_response_task():
    @http_api(
        AddHello(),
        response_shaper=lambda d: {k: v for k, v in d.items() if k not in ["context"]},
    )
    def handler(event, context):
        pass

    tested = handler
    response = tested({}, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["Hello"] == "World!"
    assert "context" not in response
    print(response)
