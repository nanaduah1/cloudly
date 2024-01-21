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
