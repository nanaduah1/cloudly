from cloudly.http.decorators import http_api
from cloudly.http.response import HttpResponse


def create_test_event(*groups):
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {"claims": {"cognito:groups": f"[{ ' '.join(groups)}]"}}
            }
        }
    }


def test_returns_403_if_user_has_no_group():
    @http_api(allow_groups=["admin"])
    def handler(event, context):
        return HttpResponse(data={"data": "ok"})

    response = handler(create_test_event(), {})

    assert response["statusCode"] == 403


def test_returns_403_if_user_in_deny_group():
    @http_api(deny_groups=["admin"])
    def handler(event, context):
        return HttpResponse(data={"data": "ok"})

    response = handler(create_test_event("admin", "sales"), {})

    assert response["statusCode"] == 403


def test_returns_200_if_user_in_deny_but_has_other_group_allowed():
    @http_api(allow_groups=["admin"], deny_groups=["sales"])
    def handler(event, context):
        return HttpResponse(data={"data": "ok"})

    response = handler(create_test_event("admin", "sales"), {})

    assert response["statusCode"] == 200


def test_returns_200_if_not_in_deny_group():
    @http_api(deny_groups=["admin"])
    def handler(event, context):
        return HttpResponse(data={"data": "ok"})

    response = handler(create_test_event("sales"), {})

    assert response["statusCode"] == 200
