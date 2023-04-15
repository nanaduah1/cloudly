import json
from dataclasses import dataclass
from abc import ABC, abstractmethod

from lambda_tools.http.validators import ValidationError


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
        return {
            "statusCode": status_code,
            "Content-Type": "application/json",
            "body": json.dumps(data) if data else "",
        }
