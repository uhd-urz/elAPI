from dataclasses import dataclass, field

from ...configuration import KEY_PLUGIN_KEY_NAME

PLUGIN_NAME: str = "mail"
PLUGIN_LINK: str = f"{KEY_PLUGIN_KEY_NAME}.{PLUGIN_NAME}".lower()


# mail plugin specific configuration
@dataclass(frozen=True)
class MailConfigKeys:
    plugin_name: str = PLUGIN_NAME.replace("-", "_")
    validate_config_early: str = "validate_config_early"
    global_email_setting: str = "global_email_setting"
    global_email_headers: str = "global_email_headers"
    cases: str = "cases"


@dataclass(frozen=True)
class MailConfigCaseKeys:
    on: str = "on"
    body: str = "body"
    headers: str = "headers"
    pattern: str = "pattern"
    target_command: str = "target_command"
    enforce_plaintext_email: str = "enforce_plaintext_email"


@dataclass(frozen=True)
class MailConfigCaseSpecialKeys:
    case_test: str = "case_test"


@dataclass(frozen=True)
class HostDefaults:
    localhost: str = "localhost"
    port: int = 25


@dataclass(frozen=True)
class MailConfigDefaultValues:
    plugin_name: dict = field(default_factory=lambda: dict())
    validate_config_early: bool = False
    global_email_setting: dict = field(default_factory=lambda: dict())
    global_email_headers: dict = field(default_factory=lambda: dict())
    cases: dict = field(default_factory=lambda: dict())


mail_config_keys = MailConfigKeys()
mail_config_case_keys = MailConfigCaseKeys()
mail_config_sp_keys = MailConfigCaseSpecialKeys()
mail_config_default_values = MailConfigDefaultValues()
host_defaults = HostDefaults()
