import pytest
from lambda_tools.http.validators import (
    DecimalNumber,
    Required,
    ValidationError,
    Validator,
)


def test_single_field_schema_with_missing_value():
    validator = Validator({"firstName": Required("firstName")})

    with pytest.raises(ValidationError):
        validator.validate({})


def test_single_field_schema_with_empty_value():
    validator = Validator({"firstName": Required("firstName")})

    with pytest.raises(ValidationError):
        validator.validate({"firstName": ""})


def test_single_field_schema_with_valid_value():
    validator = Validator({"firstName": Required("firstName")})
    cleaned = validator.validate({"firstName": "yaw"})
    assert cleaned["firstName"] == "yaw"


def test_single_field_schema_with_inner_missing_value():
    validator = Validator({"fn": Required("fn"), "inner": {"ln": Required("ln")}})

    with pytest.raises(ValidationError):
        validator.validate({"fn": "ayw", "inner": {}})


def test_single_field_schema_with_inner_valid_value():
    validator = Validator({"fn": Required("fn"), "inner": {"ln": Required("ln")}})
    cleaned = validator.validate({"fn": "ayw", "inner": {"ln": "tc"}})
    assert cleaned["inner"]["ln"] == "tc"


def test_decimal_validator_with_invalid_number():
    tested = DecimalNumber("dn")
    response = tested.validate("test")
    assert response is not None


def test_decimal_validator_with_number():
    tested = DecimalNumber("dn")
    response = tested.validate("10.00")
    assert response is None


def test_decimal_validator_with_excess_decimal_places():
    tested = DecimalNumber("dn")
    response = tested.validate("10.0099")
    assert response is not None
    assert "decimal places" in response
