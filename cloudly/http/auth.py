from functools import wraps
from typing import Any

from cloudly.http.request import RequestContext
from cloudly.http.response import HttpResponse


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
            user["username"] = response["Username"]
            return user

        return decoration

    return wrapper


def user_groups(*allow, deny: list = None):
    def wrapper(func) -> Any:
        @wraps(func)
        def decoration(event, context) -> Any:
            if not _is_authorized(event, allow, deny):
                return HttpResponse(status_code=403, data={"error": "Not authorized"})

            return func(event, context)

        def _is_authorized(event, allow, deny):
            deny_groups = deny or []
            allowed_groups = set(a for a in allow if a not in deny_groups)
            user_context = RequestContext(event)

            if not allowed_groups and deny:
                return set(deny).isdisjoint(user_context.user_groups)
            return not allowed_groups.isdisjoint(user_context.user_groups)

        return decoration

    return wrapper
