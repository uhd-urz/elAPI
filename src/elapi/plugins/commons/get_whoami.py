from enum import StrEnum

from ...api import GETRequest, GlobalSharedSession
from ...configuration import get_active_api_token, get_active_host
from ...configuration.config import APIToken
from ...loggers import Logger
from ...styles.colors import GREEN, MAGENTA, RED
from ...utils import parse_api_id_from_api_token, parse_url_only_from_host

logger = Logger()


class _ElabUserGroupColors(StrEnum):
    sysadmin = RED
    admin = MAGENTA
    user = GREEN


def get_whoami() -> dict[str, str | int | APIToken]:
    with GlobalSharedSession(limited_to="sync"):
        session = GETRequest()
        user = session("users", "me")
        user_info = user.json()
        user_all_teams = user_info["teams"]
        elab_server = session("info")
        elab_server_info = elab_server.json()
        api_keys = session("apikeys")
        api_keys_info = api_keys.json()

    elab_server_version: str = elab_server_info["elabftw_version"]
    user_full_name: str = user_info["fullname"]
    user_id: int = user_info["userid"]
    user_api_token: APIToken = get_active_api_token()
    user_api_token_id: str = parse_api_id_from_api_token(user_api_token.token)
    user_team_id: str = user_info["team"]
    user_email: str = user_info["email"]
    is_user_sysadmin: int = user_info["is_sysadmin"]
    for user_team in user_all_teams:
        if user_team["id"] == user_team_id:
            user_team_name = user_team["name"]
            user_group = user_team["usergroup"]
            break
    else:
        raise RuntimeError("User team was not found. This is an unexpected error!")
    for api_key in api_keys_info:
        if api_key["id"] == int(user_api_token_id):
            can_api_key_write = api_key["can_write"]
            break
    else:
        raise RuntimeError("API key read/write permission could not be determined!")
    return {
        "host_url": parse_url_only_from_host(get_active_host()),
        "api_token": user_api_token,
        "can_api_key_write": can_api_key_write,
        "elabftw_version": elab_server_version,
        "user_id": user_id,
        "name": user_full_name,
        "email": user_email,
        "team_id": user_team_id,
        "team": user_team_name,
        "is_sysadmin": is_user_sysadmin,
        "user_group": user_group,
    }
