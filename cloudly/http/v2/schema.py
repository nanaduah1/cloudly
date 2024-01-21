import functools
from typing import Any, Iterable, Tuple
from cloudly.http.validators import (
    Validator,
    Rule,
    ValidationError,
    string_field,
    int_field,
    decimal_field,
    boolean_field,
)


class _CustomValidator(Rule):
    def __init__(self, validator: callable):
        self._validator = validator

    def validate(self, value: Any, raw_data: dict = None) -> Tuple[Any, str]:
        try:
            cleaned_value = self._validator(value, raw_data=raw_data)
            if value and cleaned_value is None:
                raise Exception(
                    "Custom validator must return value. validate_", self.field_name
                )
            return self.valid(cleaned_value)
        except ValidationError as error:
            return self.error(str(error))


class _Field(object):
    def __init__(self, validators: Iterable[Rule]):
        self._private_name = None
        self._public_name = None
        self._validators = validators

    def __set_name__(self, owner, name):
        self._private_name = f"_{name}"
        self._public_name = name
        schema = getattr(owner, "_schema", {})
        custom_validator = self._get_custom_validator(owner, name)
        if custom_validator:
            self._validators += [_CustomValidator(custom_validator)]

        # Set field name in validators
        for validator in self._validators:
            validator.field_name = self._public_name

        schema[name] = self._validators
        owner._schema = schema

    def __get__(self, instance, owner):
        return getattr(instance, self._public_name)

    def __set__(self, instance, value):
        setattr(instance, self._private_name, value)

    def _get_custom_validator(self, instance, name):
        custom_validator = getattr(instance, f"validate_{name}", None)
        if callable(custom_validator):
            return functools.partial(custom_validator, instance)
        return None


class StringField(_Field):
    def __init__(
        self,
        required: bool = False,
        max_length: int = None,
        min_length: int = None,
        options: Iterable[str] = None,
        type: str = "text",
        pattern: str = None,
    ):
        validators = string_field(
            "",
            max=max_length,
            min=min_length,
            required=required,
            options=options,
            type=type,
            pattern=pattern,
        )
        super().__init__(validators)


class IntegerField(_Field):
    def __init__(
        self, required: bool = False, max_value: int = None, min_value: int = None
    ):
        validators = int_field("", max=max_value, min=min_value, required=required)
        super().__init__(validators)


class DecimalField(_Field):
    def __init__(
        self,
        required: bool = False,
        max_value: int = None,
        min_value: int = None,
        decimal_places: int = 2,
    ):
        validators = decimal_field(
            "",
            max=max_value,
            min=min_value,
            required=required,
            decimal_places=decimal_places,
        )
        super().__init__(validators)


class BooleanField(_Field):
    def __init__(self, required: bool = False, default_value: bool = None):
        validators = boolean_field("", required=required, default_value=default_value)
        super().__init__(validators)


class EmailField(_Field):
    def __init__(
        self, required: bool = False, max_length: int = None, min_length: int = None
    ):
        validators = string_field(
            "", required=required, type="email", max=max_length, min=min_length
        )
        super().__init__(validators)


class _ValidatorMixin(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.error = None

    def is_valid(self) -> bool:
        data = self.__dict__
        schema = self._schema
        if not schema:
            return True

        validator = Validator(schema)
        try:
            self.cleaned_data = validator.validate(data)
        except ValidationError as error:
            self.error = error
            return False
        except Exception as error:
            self.error = error
            return False
        return True


class Schema(_ValidatorMixin):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
