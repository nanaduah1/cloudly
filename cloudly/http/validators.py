import json
from decimal import Decimal
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


class ValidationError(Exception):
    pass


@dataclass
class Rule(ABC):
    field_name: str = None

    @abstractmethod
    def validate(self, value: Any, raw_data: dict = None) -> str:
        pass

    def error(self, message) -> str:
        return f"{self.field_name}: {message}"


@dataclass
class Validator:
    schema: Dict[str, Union[Rule, Dict[str, Rule]]]

    def validate(self, data: dict):
        input = {**data}
        cleaned_data, errors = self._run_validators(data=input, schema=self.schema)
        if errors:
            raise ValidationError(json.dumps(errors))
        return cleaned_data

    def _run_validators(self, data: dict, schema: dict) -> Tuple[dict, List[str]]:
        errors = []
        input_data = data or {}
        for field, validator in schema.items():
            if not validator:
                continue

            value = input_data.get(field)

            if isinstance(validator, dict):
                cleaned_value, inner_errors = self._run_validators(
                    schema=validator,
                    data=value,
                )
                errors += inner_errors
                input_data[field] = cleaned_value
            else:
                field_validators = validator
                if issubclass(field_validators.__class__, Rule):
                    field_validators = [validator]

                errors += [
                    e for e in (v.validate(value) for v in field_validators) if e
                ]

        return input_data, errors


class Required(Rule):
    def validate(self, value: Any, **kwargs) -> str:
        if not value:
            return self.error("value is required")


@dataclass
class MinLength(Rule):
    min: int = 0

    def validate(self, value: Any, **kwargs) -> str:
        if self.min and isinstance(value.__class__, str) and len(value) < self.min:
            return self.error(f"must be at least {self.min}")


@dataclass
class MaxLength(Rule):
    max: int = None

    def validate(self, value: Any, **kwargs) -> str:
        if self.max and isinstance(value.__class__, str) and len(value) > self.max:
            return self.error(f"must be at most {self.max}")


class Email(Rule):
    def validate(self, value: Any, raw_data: dict = None) -> str:
        if value and ("@" not in value or "." not in value):
            return self.error("not a valid email")


@dataclass
class DecimalNumber(Rule):
    decimal_places: int = 2

    def validate(self, value: Any, raw_data: dict = None) -> str:
        try:
            cleaned_value = Decimal(value)
            _, point = str(cleaned_value).split(".")
            if len(point) > self.decimal_places:
                return self.error(f"must be {self.decimal_places} decimal places")
        except Exception:
            return self.error("must be a decimal")


@dataclass
class IntegerNumber(Rule):
    max: Optional[int] = None
    min: Optional[int] = None

    def validate(self, value: Any, raw_data: dict = None) -> str:
        try:
            cleaned_value = int(value)
            if self.min and cleaned_value < self.min:
                return self.error(f"cannot be less than {self.min}")
            if self.max and cleaned_value > self.max:
                return self.error(f"cannot be more than {self.max}")
        except Exception:
            return self.error(f"must be an integer between{self.max} and {self.max}")


def string_field(name: str, min=None, max=None, required=False):
    validators = []
    if required is True:
        validators.append(Required(name))
    if min:
        validators.append(MinLength(name, min))
    if max:
        validators.append(MaxLength(name, max))

    return validators
