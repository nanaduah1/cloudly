import json
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Callable, List
from flowfast.base import Step
from flowfast.workflow import Workflow
from functools import wraps

from cloudly.http.validators import RunValidation, ValidationError
from cloudly.http.response import HttpResponse


@dataclass
class HttpRequest(ABC):
    event: dict

    def dispatch(self):
        try:
            data = json.loads(self.event.get("body", "{}"))
            cleaned_data = self.validate(data)
            record = self.execute(cleaned_data)
            return self.respond(data=record.get("data"))
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


def http_api(
    *args: List[Step],
    validation_schema=None,
    status=200,
    response_shaper: Callable[[Any], Any] = None
):
    def wrapper(func) -> Any:
        @wraps(func)
        def decoration(event, context) -> Any:
            try:
                all_steps = tuple(args)

                # Insert validation as first step
                if validation_schema:
                    all_steps = (RunValidation(validation_schema),) + all_steps

                if not all_steps:
                    return HttpResponse()

                first_step = all_steps[0]
                func_response = func(event, context)
                request_data = {
                    **event,
                    "context": context,
                }

                # Add the function response if any
                if func_response:
                    request_data["context"]["step_0"] = func_response

                pipeline = Workflow(first_step)
                for step in all_steps[1:]:
                    pipeline = pipeline.next(step)

                result = pipeline.run(request_data)
                final_shape = response_shaper(result) if response_shaper else result
                return HttpResponse(status, final_shape)

            except ValidationError as ex:
                return HttpResponse(400, {"error": str(ex)})
            except Exception as ex:
                print(ex)
                return HttpResponse(
                    status_code=500,
                    data={"error": "We hit a snag processing your request."},
                )

        return decoration

    return wrapper
