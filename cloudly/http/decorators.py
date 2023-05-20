from functools import wraps
from typing import Any, Callable, List
from flowfast.step import Step

from cloudly.http.request import AwsLambdaApiHandler


def http_api(
    *args: List[Step],
    validation_schema=None,
    status=200,
    clean_response: Callable[[Any], Any] = None,
    allow_groups: list = None,
    deny_groups: list = None
):
    def wrapper(func) -> Any:
        @wraps(func)
        def decoration(event, context) -> Any:
            func(event, context)
            return AwsLambdaApiHandler(
                event,
                args,
                validation_schema,
                clean_response,
                allow_groups,
                deny_groups,
            ).dispatch(status)

        return decoration

    return wrapper
