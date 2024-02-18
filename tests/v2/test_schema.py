import pytest
from cloudly.http import schema


def test_that_we_can_define_schema():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    user = User(name="test")
    assert user.is_valid() is True


def test_that_we_can_define_schema_with_invalid_data():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    user = User(name="testtesttesttest")
    assert user.is_valid() is False
    assert str(user.error) == "name: must be at most 10"


def test_that_we_invalid_email_fails():
    class User(schema.Schema):
        email = schema.EmailField(required=True, max_length=10, min_length=5)

    user = User(email="test")
    assert user.is_valid() is False
    assert str(user.error) == "email: must be at valid email address"


def test_custom_validation_called():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

        def validate_name(self, name, **kwargs):
            if name == "test":
                raise schema.ValidationError("must not be test")
            return name

    user = User(name="test")
    assert user.is_valid() is False
    assert str(user.error) == "name: must not be test"


def test_validate_method_called():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

        def validate(self, data):
            if data["name"] == "test":
                raise schema.ValidationError("must not be test")
            return data

    user = User(name="test")
    assert user.is_valid() is False
    assert str(user.error) == "must not be test"


def test_that_we_can_define_schema_with_nested_schema():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    class CarSchema(schema.Schema):
        owner = schema.ObjectField(User, required=True)

    user_list = CarSchema(owner={"name": "test"})
    assert user_list.is_valid() is True
    assert user_list.cleaned_data == {"owner": {"name": "test"}}


def test_that_we_can_define_schema_with_nested_schema_with_invalid_data():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    class CarSchema(schema.Schema):
        owner = schema.ObjectField(User, required=True)

    user_list = CarSchema(owner={"name": ""})
    assert user_list.is_valid() is False
    assert str(user_list.error) == "owner: name: value is required"


def test_that_we_can_required_nested_schema_with_missing_value_fails():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    class CarSchema(schema.Schema):
        owner = schema.ObjectField(User, required=True)
        tyres = schema.IntegerField(required=True)

    user_list = CarSchema(tyres=3)
    assert user_list.is_valid() is False
    assert str(user_list.error) == "owner: value is required"


def test_that_we_can_define_schema_with_nested_schema_with_list():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    class CarSchema(schema.Schema):
        owner = schema.ListField(User, required=True)

    user_list = CarSchema(owner=[{"name": "test"}])
    assert user_list.is_valid() is True
    assert user_list.cleaned_data == {"owner": [{"name": "test"}]}


def test_that_we_can_define_schema_with_nested_schema_with_list_with_invalid_data():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    class CarSchema(schema.Schema):
        owner = schema.ListField(User, required=True)

    user_list = CarSchema(owner=[{"name": ""}])
    assert user_list.is_valid() is False
    assert str(user_list.error) == "owner: name: value is required"


def test_that_we_can_define_schema_with_nested_schema_with_list_with_multiple_values():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    class CarSchema(schema.Schema):
        owner = schema.ListField(User, required=True)

    user_list = CarSchema(owner=[{"name": "test"}, {"name": "test2"}])
    assert user_list.is_valid() is True
    assert user_list.cleaned_data == {"owner": [{"name": "test"}, {"name": "test2"}]}


def test_read_schema_data():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    user = User(name="test")
    with pytest.raises(AttributeError):
        print(user.name)


def test_can_access_values_after_is_valid():
    class User(schema.Schema):
        name = schema.StringField(required=True, max_length=10, min_length=5)

    user = User(name="test")
    user.is_valid()
    assert user.name == "test"
