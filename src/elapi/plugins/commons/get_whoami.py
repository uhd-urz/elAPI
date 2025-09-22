from enum import StrEnum
from json import JSONDecodeError

from httpx import HTTPError

from ...api import GETRequest, SimpleClient
from ...api.validators import ElabScopes, ElabUserGroups
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


def get_whoami() -> dict[str, str | int | APIToken | dict[str, int]]:
    client = SimpleClient(is_async_client=False)
    session = GETRequest(shared_client=client)
    user = session("users", "me")
    user_info = user.json()
    elab_server = session("info")
    elab_server_info = elab_server.json()
    api_keys = session("apikeys")
    api_keys_info = api_keys.json()
    client.close()
    if not user.is_success or not elab_server.is_success or not api_keys.is_success:
        raise RuntimeError(
            "Retrieving information about the current user, "
            f"the ElabFTW server, or API keys for '{get_whoami.__name__}' "
            f"was unsuccessful. HTTP status codes: {user.status_code}, "
            f"{elab_server.status_code}, {api_keys.status_code}."
        )

    user_all_teams = user_info["teams"]
    elab_server_version: str = elab_server_info["elabftw_version"]
    user_full_name: str = user_info["fullname"]
    user_id: int = user_info["userid"]
    user_api_token: APIToken = get_active_api_token()
    user_api_token_id: str = parse_api_id_from_api_token(user_api_token.token)
    user_team_id: str = user_info["team"]
    user_email: str = user_info["email"]
    is_user_sysadmin: int = user_info["is_sysadmin"]
    scope_experiments: int = user_info["scope_experiments"]
    scope_items = user_info["scope_items"]
    scope_experiments_templates = user_info["scope_experiments_templates"]
    scope_teamgroups = user_info["scope_teamgroups"]
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
        "scopes": {
            "experiments": scope_experiments,
            "items": scope_items,
            "experiments_templates": scope_experiments_templates,
            "teamgroups": scope_teamgroups,
        },
    }


def debug_log_whoami_message() -> None:
    try:
        (
            host_url,
            api_token,
            can_api_key_write,
            elabftw_version,
            user_id,
            name,
            email,
            team_id,
            team,
            is_sysadmin,
            user_group,
            scopes,
        ) = get_whoami().values()
    except (RuntimeError, HTTPError, JSONDecodeError) as e:
        logger.warning(
            f"Fetching '{get_whoami.__name__}' information has failed with "
            f"the following error: {e!r}"
        )
        return
    user_groups_reversed: dict[int, str] = {
        v: k for k, v in ElabUserGroups.__members__.items()
    }
    scopes_reversed: dict[int, str] = {v: k for k, v in ElabScopes.__members__.items()}
    logger.debug(
        f"Based on the detected configuration, the requests will be made to the server {host_url} "
        f"(eLabFTW version: {elabftw_version}), "
        f"with API token '{api_token}' ({'Read/Write' if can_api_key_write else 'Read-only'}), "
        f"by user '{name}' (ID: {user_id}), "
        f"from team '{team}' (ID: {team_id}), in user group "
        f"'{user_groups_reversed[user_group].capitalize()}', "
        f"{'as a sysadmin' if is_sysadmin else 'not as a sysadmin'}. Scopes: "
        f"experiments = '{scopes_reversed[scopes['experiments']].capitalize()}', "
        f"items = '{scopes_reversed[scopes['items']].capitalize()}', "
        f"experiments_templates = '{scopes_reversed[scopes['experiments_templates']].capitalize()}', "
        f"teamgroups = '{scopes_reversed[scopes['teamgroups']].capitalize()}'."
    )
