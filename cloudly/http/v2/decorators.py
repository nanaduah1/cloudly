from functools import wraps
from cloudly.http.v2.api import Response, Request, User


def user_required(*groups):
    import boto3

    cognito_client = boto3.client("cognito-idp")

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, request: Request, *args, **kwargs):
            user = _get_user(request)
            if user:
                user_groups = request.context.user_groups
                if not groups or any(group in user_groups for group in groups):
                    request.set("user", User(user))
                    return decorated(self, request, *args, **kwargs)
            return Response("Unauthorized", status=401)

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
