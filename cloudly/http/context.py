from typing import List, Optional, Union


class RequestContext:
    def __init__(self, event: dict):
        self._ctx = event.get("requestContext", {})

    @property
    def user_groups(self) -> Union[List[str], None]:
        groups = (
            self._ctx.get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
            .get("cognito:groups")
        )

        if groups and isinstance(groups, str):
            return groups[1:-1].split(",")

    @property
    def client_id(self) -> Optional[str]:
        return (
            self._ctx.get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
            .get("client_id")
        )

    @property
    def username(self) -> Optional[str]:
        return (
            self._ctx.get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
            .get("username")
        )

    @property
    def account_id(self) -> Optional[str]:
        return self._ctx.get("accountId")

    @property
    def app_id(self) -> Optional[str]:
        return self._ctx.get("appId")

    @property
    def client_ip_address(self) -> Optional[str]:
        return self._ctx.get("http", {}).get("sourceIp")

    @property
    def path(self) -> Optional[str]:
        return self._ctx.get("http", {}).get("path")
