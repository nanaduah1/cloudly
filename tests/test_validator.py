from decimal import Decimal
from datetime import datetime
import pytest
from cloudly.http.validators import (
    DecimalNumber,
    IntegerNumber,
    Required,
    ValidationError,
    Validator,
    decimal_field,
    list_field,
    string_field,
    BooleanValidator,
    boolean_field
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
    validator = Validator(
        {"fn": Required("fn"), "inner": {"ln": Required("ln")}})

    with pytest.raises(ValidationError):
        validator.validate({"fn": "ayw", "inner": {}})


def test_single_field_schema_with_inner_valid_value():
    validator = Validator(
        {"fn": Required("fn"), "inner": {"ln": Required("ln")}})
    cleaned = validator.validate({"fn": "ayw", "inner": {"ln": "tc"}})
    assert cleaned["inner"]["ln"] == "tc"


def test_boolean_validator_with_string():
    tested = BooleanValidator("is_true", True)
    response = tested.validate("false")
    assert response is not None


def test_boolean_validator_with_number():
    tested = BooleanValidator("is_true", True)
    v, error = tested.validate(10)
    assert "required" in error


def test_boolean_validator_with_datetime():
    tested = BooleanValidator("is_true", True)
    v, error = tested.validate(datetime.now())
    assert "required" in error


def test_boolean_validator_with_True():
    tested = BooleanValidator("is_true", True)
    v, error = tested.validate(True)
    assert error is None
    assert isinstance(v, bool)


def test_boolean_validator_with_False():
    tested = BooleanValidator("is_true", True)
    v, error = tested.validate(False)
    assert error is None
    assert isinstance(v, bool)


def test_boolean_validator_with_None():
    tested = BooleanValidator("is_true", True)
    v, error = tested.validate(None)
    assert error is None
    assert isinstance(v, bool)


def test_decimal_validator_with_invalid_number():
    tested = DecimalNumber("dn")
    response = tested.validate("test")
    assert response is not None


def test_decimal_validator_with_number():
    tested = DecimalNumber("dn")
    v, error = tested.validate("10.00")
    assert error is None
    assert isinstance(v, Decimal)


def test_decimal_validator_with_excess_decimal_places():
    tested = DecimalNumber("dn")
    value, error = tested.validate("10.0099")
    assert error is not None
    assert "decimal places" in error


def test_string_field():
    validation_schema = {
        "contact": {
            "firstName": string_field("firstName", required=True),
            "lastName": string_field("lastName", required=True),
            "phoneNumber": string_field("phoneNumber", required=True, max=10, min=10),
        },
        "business": {
            "name": string_field("name", required=True),
            "address": string_field("address", required=True),
            "city": string_field("city", required=True),
            "country": string_field("country", required=True),
        },
    }
    tested = Validator(validation_schema)

    with pytest.raises(ValidationError):
        tested.validate({"age": 0})


def test_list_validator_is_optional():
    schema = {
        "name": string_field("name", required=True),
        "options": list_field("options"),
    }

    Validator(schema).validate({"name": "Yellow"})


def test_required_list_fails():
    schema = {
        "name": string_field("name", required=True),
        "options": list_field("options", required=True),
    }

    with pytest.raises(ValidationError):
        Validator(schema).validate({"name": "Yellow"})


def test_min_list_validation():
    schema = {
        "name": string_field("name", required=True),
        "options": list_field("options", min_items=1),
    }

    with pytest.raises(ValidationError):
        Validator(schema).validate({"name": "Yellow"})


def test_max_length_fails():
    schema = {
        "name": string_field("name", required=True),
        "options": list_field("options", max_items=1),
    }

    with pytest.raises(ValidationError):
        Validator(schema).validate({"name": "Yellow", "options": [{}, {}]})


def test_item_schema_validates():
    schema = {
        "options": list_field(
            "options", item_schema={"name": string_field("options.name", required=True)}
        ),
    }

    with pytest.raises(ValidationError):
        Validator(schema).validate({"name": "Yellow", "options": [{}]})


def test_item_schema_validation_cleans_values():
    schema = {
        "options": list_field(
            "options",
            item_schema={
                "price": decimal_field("options.price", required=True),
                "sls": list_field(
                    "options.sls",
                    required=True,
                    item_schema={
                        "size": decimal_field("options.sls.size", required=True)
                    },
                ),
            },
        ),
    }

    response = Validator(schema).validate(
        {"options": [{"price": "10.00", "sls": [{"size": "2.00"}]}]}
    )
    assert response["options"][0]["price"] == Decimal("10.00")
    assert response["options"][0]["sls"][0]["size"] == Decimal("2.00")


def test_validator_cleans_value():
    schema = {
        "amount": DecimalNumber("amount"),
        "payer": {"age": IntegerNumber("age")},
    }

    response = Validator(schema).validate(
        {"amount": 10.99, "payer": {"age": "10"}})

    assert response["amount"] == Decimal("10.99")
    assert response["payer"]["age"] == 10
