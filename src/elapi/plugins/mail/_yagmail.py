import inspect
from dataclasses import dataclass

import yagmail


@dataclass(frozen=True)
class RequiredEmailSettingParams:
    host: str = "host"
    port: str = "port"


@dataclass(frozen=True)
class RequiredEmailHeadersParams:
    from_: str = "from"
    to: str = "to"


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


required_email_setting_params = RequiredEmailSettingParams()
required_email_headers_params = RequiredEmailHeadersParams()
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
            param not in required_email_setting_params.__dict__.values()
            and param not in yagmail_smtp_unused_params.__dict__.values()
        ):
            additional_yagmail_smtp_class_params.append(param)
    return additional_yagmail_smtp_class_params
