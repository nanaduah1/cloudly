from functools import wraps
from cloudly.http.v2.api import HttpError, Request, User


def user_required(groups=None):
    import boto3

    cognito_client = boto3.client("cognito-idp")

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, request: Request, **kwargs):
            user = _get_user(request)
            if not user:
                raise HttpError("Unauthorized", 401)

            if groups and "cognito:groups" not in user:
                raise HttpError("Forbidden", 403)
            if groups and not any(group in user["cognito:groups"] for group in groups):
                raise HttpError("Forbidden", 403)
            request.set("user", User(user))
            return decorated(self, request, **kwargs)

        return wrapper

    def _get_user(request: Request):
        if not request.headers or "authorization" not in request.headers:
            return None

        _, accessToken = request.headers.get("authorization", "").split(" ")
        if not accessToken:
            return None

        response = cognito_client.get_user(AccessToken=accessToken)
        user = {attr["Name"]: attr["Value"] for attr in response["UserAttributes"]}
        user["username"] = response["Username"]
        return user

    return decorator
