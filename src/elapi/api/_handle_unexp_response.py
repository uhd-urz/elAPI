import json

from ..loggers import Logger
from ..utils import UnexpectedAPIResponseType
from ._names import ElabUserGroups

logger = Logger()
NewUserTeamsType = list[dict[str, int | bool | str]]

_DEBUG_LOG_EMIT_ONCE: bool = False


def handle_new_user_teams(user_teams: str | NewUserTeamsType) -> NewUserTeamsType:
    global _DEBUG_LOG_EMIT_ONCE

    struct_user_teams: list[dict[str, int | bool | str]] = []
    match user_teams:
        case list():
            struct_user_teams = user_teams
        case str():
            try:
                struct_user_teams = json.loads(user_teams)
            except json.JSONDecodeError as e:
                raise UnexpectedAPIResponseType(
                    "Given user_teams is a string, but it could not be "
                    f"parsed as a valid JSON. Exception: {e}"
                ) from e
        case _:
            raise UnexpectedAPIResponseType(
                f"Given user_teams type '{type(user_teams)}' is not supported."
            )
    for user_team in struct_user_teams:
        try:
            user_group = user_team["usergroup"]
        except KeyError:
            try:
                user_group = ElabUserGroups.get_group_from_admin_status(
                    bool(user_team["is_admin"])
                )
            except KeyError as e:
                raise UnexpectedAPIResponseType(
                    "user_team doesn't have 'usergroup', so a "
                    "'is_admin' field was expected. "
                    f"But no 'is_admin' is found either! User team: {user_team}"
                ) from e
            else:
                if _DEBUG_LOG_EMIT_ONCE is False:
                    logger.debug(
                        "Field 'usergroup' is not found in user team info. "
                        "This likely means the eLabFTW version is using a "
                        "newer API version. 'is_admin' field is found and has "
                        "been used instead."
                    )
                _DEBUG_LOG_EMIT_ONCE = True
                user_team["usergroup"] = user_group
        else:
            pass
    return struct_user_teams
