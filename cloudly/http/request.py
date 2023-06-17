import json
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, List
from flowfast.base import Step
from flowfast.workflow import Workflow
from cloudly.http.context import RequestContext
from cloudly.http.exceptions import NotAuthorizedError
from cloudly.http.security import user_groups

from cloudly.http.validators import ValidationError, Validator
from cloudly.http.response import HttpResponse

from typing import List

from cloudly.logging.logger import Logger


@dataclass
class HttpRequest(ABC):
    event: dict
    allow_groups: list = None
    deny_groups: list = None
    logger: Logger = None

    def dispatch(self, status_code=200):
        try:
            # IMPORTANT: Must be first statement in the execution
            self._check_permissions()

            data = json.loads(self.event.get("body", "{}"))
            cleaned_data = self.validate(data)
            record = self.execute(cleaned_data)
            return self.respond(data=record, status_code=status_code)
        except ValidationError as ex:
            self.logger and self.logger.exception("Validation failed", ex)
            return self.respond(
                status_code=400,
                data={"error": str(ex)},
            )
        except NotAuthorizedError as ex:
            self.logger and self.logger.exception("Unauthorized", ex)
            return HttpResponse(status_code=403, data={"error": "Not authorized"})
        except Exception as ex:
            self.logger and self.logger.exception("Handled Exception", ex)
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

    def _check_permissions(self):
        user_groups(
            self.event,
            self.allow_groups or [],
            self.deny_groups,
        )


@dataclass
class AwsLambdaApiHandler(HttpRequest):
    logger: Logger = None
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
        for step in all_steps[1:]:
            pipeline = pipeline.next(step)

        result = pipeline.run(request_data)
        cleaned_result = self.clean_response(result) if self.clean_response else result
        return self._exclude_metadata(cleaned_result)

    def validate(self, data: dict) -> dict:
        if not self.validation_schema:
            return data
        return Validator(self.validation_schema).validate(data)

    def _exclude_metadata(self, results: dict):
        if results is None:
            return

        if isinstance(results, dict):
            return {k: v for k, v in results.items() if k not in ["_request"]}

        return results
