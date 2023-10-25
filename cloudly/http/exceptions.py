class ValidationError(Exception):
    pass


class NotAuthorizedError(Exception):
    pass


class HttpResponseError(Exception):
    def __init__(self, status_code: int, data: dict):
        self.status_code = status_code
        self.data = data
        super().__init__(f"HTTP {status_code}")
