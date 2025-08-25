import inspect
from dataclasses import dataclass
from getpass import getuser
from pathlib import Path
from socket import getfqdn
from typing import Optional

import yagmail

from ...loggers import Logger
from .names import host_defaults

logger = Logger()


@dataclass(frozen=True)
class MainEmailSettingParams:
    host: str = "host"
    port: str = "port"


@dataclass(frozen=True)
class MainEmailSettingFallbackValues:
    host: str = host_defaults.localhost
    port: int = host_defaults.port


@dataclass(frozen=True)
class RequiredEmailHeadersParams:
    To: str = "to"


@dataclass(frozen=True)
class RequiredEmailHeadersWithFallbackParams:
    From: str = "from"


@dataclass(frozen=True)
class YagMailSMTPUnusedParams:
    user: str = "user"
    kwargs: str = "kwargs"
    soft_email_validation: str = "soft_email_validation"


@dataclass
class YagMailSendParams:
    to: list[str]
    contents: str
    headers: dict[str, str]
    message_id: str
    group_messages: bool = True
    prettify_html: bool = True


main_email_setting_params = MainEmailSettingParams()
main_email_setting_fallback_values = MainEmailSettingFallbackValues()
required_email_headers_params = RequiredEmailHeadersParams()
required_email_headers_fallback_params = RequiredEmailHeadersWithFallbackParams()
yagmail_smtp_unused_params = YagMailSMTPUnusedParams()


def get_accepted_yagmail_smtp_class_params() -> list[str]:
    yagmail_smtp_class_params: list[str] = list(
        inspect.signature(yagmail.SMTP).parameters.keys()
    )
    for param in yagmail_smtp_unused_params.__dict__.values():
        yagmail_smtp_class_params.remove(param)
    return yagmail_smtp_class_params


def get_additional_yagmail_smtp_class_params() -> list[str]:
    additional_yagmail_smtp_class_params: list[str] = []
    for param in get_accepted_yagmail_smtp_class_params():
        if (
            param not in main_email_setting_params.__dict__.values()
            and param not in yagmail_smtp_unused_params.__dict__.values()
        ):
            additional_yagmail_smtp_class_params.append(param)
    return additional_yagmail_smtp_class_params


def _get_fqdn() -> Optional[str]:
    try:
        return getfqdn()
    # Though Python documentation doesn't explicitly state that an OSError can happen,
    # but given that getpass.getuser() can throw OSError, we're assuming an
    # OSError is feasible.
    except OSError:
        logger.debug("Could not read FQDN via Python's socket.getfqdn().")
        return None


def _get_fallback_from_origin() -> Optional[str]:
    fqdn: Optional[str] = _get_fqdn()
    mailname_path: Path = Path("/etc/mailname")  # not supported in Windows
    try:
        origin: str = mailname_path.read_text().strip()
    except (FileNotFoundError, ValueError, IsADirectoryError) as e:
        logger.debug(
            f"File path {mailname_path} could not be read for setting header "
            f"'{required_email_headers_fallback_params.From}' value. "
            f"Exception details: {e}"
        )
        return fqdn
    else:
        if not origin:
            logger.debug(
                f"File path {mailname_path} content is empty. Empty value will not be used for"
                f"'{required_email_headers_fallback_params.From}' header."
            )
            return fqdn
        return origin


def _get_host_user() -> Optional[str]:
    try:
        user: Optional[str] = getuser()
    except OSError:
        logger.debug("Could not read host username via Python's getpass.getuser().")
        return None
    else:
        return user


def _get_formatted_fallback_from_email_address() -> Optional[str]:
    host_user: Optional[str] = _get_host_user()
    email_address: Optional[str] = _get_fallback_from_origin()
    if host_user is None:
        return email_address
    if email_address is None:
        return None
    return f"{host_user.capitalize()} <{host_user.lower()}@{email_address}>"
