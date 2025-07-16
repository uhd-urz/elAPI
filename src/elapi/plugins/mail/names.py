from dataclasses import dataclass

from ...configuration import KEY_PLUGIN_KEY_NAME

PLUGIN_NAME: str = "mail"
PLUGIN_LINK: str = f"{KEY_PLUGIN_KEY_NAME}.{PLUGIN_NAME}".lower()


# mail plugin specific configuration
@dataclass
class MailConfigKeys:
    plugin_name: str = PLUGIN_NAME.replace("-", "_")
    validate_early: str = "validate_early"
    global_email_setting: str = "global_email_setting"
    global_email_headers: str = "global_email_headers"
    cases: str = "cases"


@dataclass
class MailConfigCaseKeys:
    on: str = "on"
    body: str = "body"
    headers: str = "headers"
    pattern: str = "pattern"
    target_command: str = "target_command"
    enforce_plaintext_email: str = "enforce_plaintext_email"


@dataclass
class MailConfigCaseSpecialKeys:
    case_test: str = "case_test"
