# Version 2.0.0

The original version of the library was written to wrap some of the repetitive tasks I was doing
when writing python based lambda functions and API Gateway endpoints. It was also a way to learn.

This version builds on the original version and adds some new features and changes some of the old ones.
Below are some of the goals of this version:

1.  Make it easier to write lambda functions and API Gateway endpoints using python. Ideally, validation of the request, parsing of the request, and response handling should be as easy as possible.

2.  Make it possible to run the same code locally and in the cloud. This means that the code should be able to run in a lambda function and also in a local environment. This is important for testing and debugging.

## Stretch goals

3.  Ability to generate CDK code for the lambda functions and API Gateway endpoints. This is important for infrastructure as code.

4.  Ability to generate OpenAPI documentation for the API Gateway endpoints. This is important for API documentation.

## Getting started

1. Install the library in your project

   ```bash
   poetry add git+https://github.com/nanaduah1/cloudly.git@version
   ```

# Example usage (class style)

```python
from cloudly.http import Request, Response
from cloudly.http import HttpApi

class Handler(HttpApi):
    def get(self, request: Request):
        return Response(body={"message": "Hello world!"})

    def post(self, request: Request):
        return Response(body={"message": "Hello world!"})

    def put(self, request: Request):
        return Response(body={"message": "Hello world!"})

    def delete(self, request: Request):
        return Response(body={"message": "Hello world!"})

    def patch(self, request: Request):
        return Response(body={"message": "Hello world!"})

    def head(self, request: Request):
        return Response(body={"message": "Hello world!"})

    def options(self, request: Request):
        return Response(body={"message": "Hello world!"})

handler = Handler()
```

# Example usage (class style with Model)

```python
from cloudly.http import Request, Response
from cloudly.http import HttpApi

class User(Model):
    name: str
    age: int

class UserSchema(Schema):
      name = fields.String(required=True)
      age = fields.Integer(required=True)

      def validate_age(self, value):
         if value < 0:
              raise ValidationError("Age must be greater than 0")
         return value
      def validate_name(self, value):
         if len(value) < 3:
            raise ValidationError("Name must be at least 3 characters")
         return value

      def validate(self, data):
         if data["name"] == "John" and data["age"] < 18:
            raise ValidationError("John must be at least 18 years old")


class Handler(HttpApi):
   model = User
   schema = UserSchema

```
