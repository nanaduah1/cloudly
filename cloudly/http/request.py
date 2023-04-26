import json
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, List
from flowfast.base import Step
from flowfast.workflow import Workflow
from functools import wraps

from cloudly.http.validators import ValidationError, Validator
from cloudly.http.response import HttpResponse

from typing import List, Optional, Union
from flowfast.step import Task, Mapping


class RequestContext:
    def __init__(self, event: dict):
        self._ctx = event.get("requestContext", {})

    @property
    def user_groups(self) -> Union[List[str], None]:
        return (
            self._ctx.get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
            .get("cognito:groups", [])
        )

    @property
    def client_id(self) -> Optional[str]:
        return (
            self._ctx.get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
            .get("client_id")
        )

    @property
    def username(self) -> Optional[str]:
        return (
            self._ctx.get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
            .get("username")
        )

    @property
    def account_id(self) -> Optional[str]:
        return self._ctx.get("accountId")

    @property
    def app_id(self) -> Optional[str]:
        return self._ctx.get("appId")

    @property
    def client_ip_address(self) -> Optional[str]:
        return self._ctx.get("http", {}).get("sourceIp")

    @property
    def path(self) -> Optional[str]:
        return self._ctx.get("http", {}).get("path")


@dataclass
class HttpRequest(ABC):
    event: dict

    def dispatch(self, status_code=200):
        try:
            data = json.loads(self.event.get("body", "{}"))
            cleaned_data = self.validate(data)
            record = self.execute(cleaned_data)
            return self.respond(data=record, status_code=status_code)
        except ValidationError as ex:
            return self.respond(
                status_code=400,
                data={"error": str(ex)},
            )
        except Exception as ex:
            print(ex)
            return self.respond(
                status_code=500,
                data={"error": "We hit a snag processing your request."},
            )

    @abstractmethod
    def validate(self, data: dict) -> dict:
        pass

    @abstractmethod
    def execute(self, cleaned_data: dict) -> dict:
        pass

    def respond(self, status_code=200, data: dict = None):
        return HttpResponse(status_code, data)


@dataclass
class AwsLambdaApiHandler(HttpRequest):
    middleware: List[Step] = None
    validation_schema: dict = None
    clean_response: Callable[[Any], Any] = None

    def execute(self, cleaned_data: dict) -> dict:
        all_steps = tuple()
        if issubclass(self.middleware.__class__, Step):
            all_steps = (self.middleware,)
        elif isinstance(self.middleware, Iterable):
            all_steps = self.middleware

        if not all_steps:
            return {}

        first_step = all_steps[0]
        request_data = {
            **cleaned_data,
            "_request": {
                "event": self.event,
                "context": RequestContext(self.event),
                "@user": self.event.get("@user"),
            },
        }

        pipeline = Workflow(first_step)
        for step in all_steps:
            pipeline = pipeline.next(step)

        result = pipeline.run(request_data)
        cleaned_result = self.clean_response(result) if self.clean_response else result
        return self._exclude_metadata(cleaned_result)

    def validate(self, data: dict) -> dict:
        if not self.validation_schema:
            return data
        return Validator(self.validation_schema).validate(data)

    def _exclude_metadata(self, response: dict):
        if response is None:
            return

        return {k: v for k, v in response.items() if k not in ["_request"]}
