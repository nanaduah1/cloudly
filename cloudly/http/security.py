from typing import Iterable
from cloudly.http.exceptions import NotAuthorizedError
from cloudly.http.context import RequestContext


def user_groups(
    event: dict,
    allow: Iterable[str],
    deny: Iterable[str] = None,
):
    deny_groups = deny or []

    # If no permissions specified then skip
    if not (allow or deny):
        return

    allowed_groups = set(a for a in allow if a not in deny_groups)
    user_context = RequestContext(event)

    authorized = False
    if not allowed_groups and deny:
        authorized = set(deny).isdisjoint(user_context.user_groups)
    else:
        authorized = not allowed_groups.isdisjoint(user_context.user_groups)

    if not authorized:
        raise NotAuthorizedError("User not authorized")
