import re
from decimal import Decimal
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from flowfast.step import Task, Mapping

from cloudly.http.exceptions import ValidationError


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
            raise ValidationError(",".join(errors))
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
    pattern = r"^\S+@\S+\.\S+$"

    def validate(self, value: Any, raw_data: dict = None) -> str:
        return RegexValidator(self.field_name, self.pattern).validate(value)


@dataclass
class DecimalNumber(Rule):
    decimal_places: int = 2
    min: str = None
    max: str = None

    def validate(self, value: Any, raw_data: dict = None) -> str:
        try:
            cleaned_value = Decimal(value)

            if "." in str(cleaned_value):
                _, point = str(cleaned_value).split(".")
                if len(point) > self.decimal_places:
                    return self.error(f"must be {self.decimal_places} decimal places")

            if self.max and cleaned_value > Decimal(self.max):
                return self.error(f"cannot be more than {self.max}")

            if self.min and cleaned_value < Decimal(self.min):
                return self.error(f"cannot be less than {self.min}")

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
            return self.error(f"must be an integer between {self.min} and {self.max}")


@dataclass
class RegexValidator(Rule):
    pattern: str = "*"

    def validate(self, value: Any, raw_data: dict = None) -> str:
        try:
            regex = re.compile(self.pattern)
            if not regex.match(value):
                return self.error(f"does not match the pattern {self.pattern}")
        except Exception:
            return self.error(f"does not match the pattern {self.pattern}")


@dataclass
class OptionsValidator(Rule):
    options: Iterable[Any] = field(default_factory=tuple)

    def validate(self, value: Any, raw_data: dict = None) -> str:
        if value and not value in self.options:
            return self.error(f"must be one of [{', '.join(self.options)}]")


def int_field(name: str, min: int = None, max: int = None, required=False):
    validators = []
    if required is True:
        validators.append(Required(name))
    validators.append(IntegerNumber(name, max, min))

    return validators


def decimal_field(
    name: str, min: str = None, max: str = None, decimal_places=2, required=False
):
    validators = []
    if required is True:
        validators.append(Required(name))
    validators.append(DecimalNumber(name, decimal_places, min, max))

    return validators


def string_field(
    name: str,
    min=None,
    max=None,
    required=False,
    type="text",
    pattern=None,
    options: Iterable[Any] = None,
):
    validators = []
    if required is True:
        validators.append(Required(name))
    if min:
        validators.append(MinLength(name, min))
    if max:
        validators.append(MaxLength(name, max))

    if type == "email":
        validators.append(Email(name))
    if pattern:
        validators.append(RegexValidator(name, pattern))

    if options:
        validators.append(OptionsValidator(name, options))

    return validators


@dataclass
class RunValidation(Task):
    schema: Mapping

    def process(self, input: Mapping) -> Mapping:
        return Validator(self.schema).validate(input)


@dataclass
class ListFieldValidator(Rule):
    item_schema: dict = None
    min_items: int = 0
    max_items: int = None

    def validate(self, value: Any, raw_data: dict = None) -> str:
        cleaned_value = value or []
        if not isinstance(cleaned_value, Iterable):
            return

        items_count = len(cleaned_value)
        if self.min_items and self.min_items > 0 and items_count < self.min_items:
            return self.error(f"must have at least {self.min_items} items")

        if self.max_items and self.max_items < items_count:
            return self.error(f"must have at most {self.max_items} items")

        if not self.item_schema or not isinstance(self.item_schema, dict):
            return

        item_validator = Validator(self.item_schema)
        try:
            for index, item in enumerate(cleaned_value):
                item_validator.validate(item)
        except ValidationError as ex:
            return self.error(f"[{index}]: {str(ex)}")


def list_field(
    name: str, min_items=None, max_items=None, required=False, item_schema: dict = None
):
    validators = []

    validators.append(ListFieldValidator(name, item_schema, min_items, max_items))
    if required:
        validators.append(Required(name))

    return validators
