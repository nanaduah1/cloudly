from functools import wraps
from typing import Any


def aws_cognito():
    import boto3

    return boto3.client("cognito-idp")


def inject_user(cognito_client: Any):
    def wrapper(func) -> Any:
        @wraps(func)
        def decoration(event, context) -> Any:
            user = _get_user(event)
            event["@user"] = user
            func(event, context)

        def _get_user(input):
            event = {**input}
            if (
                not event
                or "headers" not in event
                or "authorization" not in event["headers"]
            ):
                return None

            _, accessToken = event["headers"]["authorization"].split(" ")

            if not accessToken:
                return None

            response = cognito_client.get_user(AccessToken=accessToken)
            user = {attr["Name"]: attr["Value"] for attr in response["UserAttributes"]}
            user["username"] = response["UserName"]
            return user

        return decoration

    return wrapper
