import re
from dataclasses import dataclass

import yagmail
from yagmail.validate import DOMAIN, LOCAL_PART

from ...configuration import (
    get_active_plugin_configs,
)
from ...core_validators import Exit, ValidationError
from ...loggers import Logger
from ...path import ProperPath
from ...utils import PatternNotFoundError
from ._yagmail import (
    RequiredEmailHeadersParams,
    RequiredEmailSettingParams,
    YagMailSMTPUnusedParams,
    get_additional_yagmail_smtp_class_params,
)
from .names import MailConfigCaseKeys, MailConfigCaseSpecialKeys, MailConfigKeys

logger = Logger()
mail_config_keys = MailConfigKeys()
mail_config_sp_keys = MailConfigCaseSpecialKeys()


@dataclass
class _ValidatedEmailCases:
    real_cases: dict
    test_case: dict


_validated_email_cases = _ValidatedEmailCases(real_cases=dict(), test_case=dict())


def get_mail_config() -> dict:
    return get_active_plugin_configs().get(
        mail_config_keys.plugin_name,
        dict(),
    )


def get_mail_is_early_validation_allowed() -> bool:
    return get_mail_config().get(
        mail_config_keys.validate_early,
        True,
    )


def get_global_email_setting() -> dict:
    return get_mail_config().get(
        mail_config_keys.global_email_setting,
        dict(),
    )


def get_global_email_headers() -> dict:
    return get_mail_config().get(
        mail_config_keys.global_email_headers,
        dict(),
    )


def get_email_cases() -> dict:
    return get_mail_config().get(
        mail_config_keys.cases,
        dict(),
    )


def _parse_email_with_name(value: str) -> tuple[str, str, str]:
    if match := re.match(rf"^(.+) <({LOCAL_PART}@({DOMAIN}))>$", value, re.IGNORECASE):
        name: str = match.group(1)
        email_address: str = match.group(2)
        domain: str = match.group(3)
        return name, email_address, domain
    raise PatternNotFoundError


def _parse_email_only(value: str) -> tuple[str, str]:
    if match := re.match(rf"^({LOCAL_PART}@({DOMAIN}))$", value, re.IGNORECASE):
        email_address: str = match.group(1)
        domain: str = match.group(2)
        return email_address, domain
    raise PatternNotFoundError


def get_structured_email_cases() -> tuple[dict, dict]:
    global_email_setting: dict = get_global_email_setting()
    st_cases: dict = {}
    mail_config_case_keys = MailConfigCaseKeys()
    for case_name, case_val in get_email_cases().items():
        st_cases[case_name] = {}
        case_on = case_val.get(mail_config_case_keys.on)
        case_pattern = case_val.get(mail_config_case_keys.pattern)
        if case_on is None and case_pattern is None:
            if case_name != mail_config_sp_keys.case_test:
                raise ValidationError(
                    f"Either '{mail_config_case_keys.on}' or "
                    f"'{mail_config_case_keys.pattern}' "
                    f"or both must be provided for case {case_name}."
                )
        if case_on is not None:
            if case_name == mail_config_sp_keys.case_test:
                logger.info(
                    f"Email case '{case_name}' is special, and "
                    f"'{case_name}.{mail_config_case_keys.on}' will be ignored."
                )
            elif not isinstance(case_on, list):
                raise ValidationError(
                    f"'{case_name}.{mail_config_case_keys.on}' must be a list of log levels."
                )
            st_cases[case_name][mail_config_case_keys.on] = case_on
        if case_pattern is not None:
            if case_name == mail_config_sp_keys.case_test:
                logger.info(
                    f"Email case '{case_name}' is special, and "
                    f"'{case_name}.{mail_config_case_keys.pattern}' will be ignored."
                )
            elif not isinstance(case_pattern, str):
                raise ValidationError(
                    f"'{case_name}.{mail_config_case_keys.pattern}' must be a string of "
                    f"Python regex pattern."
                )
            st_cases[case_name][mail_config_case_keys.pattern] = case_pattern
        case_body = case_val.get(mail_config_case_keys.body)
        if case_body is None:
            case_body: str = ""
            st_cases[case_name][mail_config_case_keys.body] = case_body
        else:
            try:
                case_body_path = ProperPath(case_body)
            except ValueError as e:
                raise ValidationError(
                    f"'{mail_config_keys.plugin_name}.{mail_config_case_keys.body}' "
                    f"value '{case_body}' is an invalid path value."
                ) from e
            else:
                if not (
                    case_body_path.kind == "file" or case_body_path.expanded.exists()
                ):
                    raise ValidationError(
                        f"'{mail_config_keys.plugin_name}.{mail_config_case_keys.body}' "
                        f"value '{case_body_path}' is not a file path or "
                        f"does not exist."
                    )
                case_body: str = case_body_path.expanded.read_text()
                st_cases[case_name][mail_config_case_keys.body] = case_body
        st_cases[case_name]["main_params"] = {}
        for required_param in RequiredEmailSettingParams().__dict__.values():
            required_param_value = case_val.get(
                required_param
            ) or global_email_setting.get(required_param)
            if required_param_value is None:
                raise ValidationError(
                    f"'{case_name}.{required_param}' "
                    f"value cannot be null and must be provided!"
                )
            st_cases[case_name]["main_params"][required_param] = required_param_value
        for additional_param in get_additional_yagmail_smtp_class_params():
            additional_param_value = case_val.get(
                additional_param
            ) or global_email_setting.get(additional_param)
            if additional_param_value is not None:
                st_cases[case_name]["main_params"][additional_param] = (
                    additional_param_value
                )
        for unused_param in YagMailSMTPUnusedParams().__dict__.values():
            if case_val.get(unused_param) is not None:
                raise ValidationError(
                    f"'{case_name}.{unused_param}' cannot be used in this context."
                )
        case_headers = case_val.get(mail_config_case_keys.headers, dict())
        case_headers_lower = {k.lower(): v for k, v in case_headers.items()}
        global_email_headers_lower = {
            k.lower(): v for k, v in get_global_email_headers().items()
        }
        required_headers_names = RequiredEmailHeadersParams()
        st_cases[case_name]["headers"] = {}
        for header_name, header_value in case_headers_lower.items():
            header_name: str = header_name.lower()
            header_value = header_value or global_email_headers_lower.get(header_name)
            if header_name in required_headers_names.__dict__.values():
                if header_value is None:
                    raise ValidationError(
                        f"'{case_name}.{mail_config_case_keys.headers}.{header_name.capitalize()}' "
                        f"header must must be provided!"
                    )
            if header_name == required_headers_names.from_:
                if not isinstance(header_value, str):
                    raise ValidationError(
                        f"'{case_name}.{mail_config_case_keys.headers}.{header_name.capitalize()}' "
                        f"header must be a string. "
                        f"E.g., 'Jane Doe <jane.doe@localhost.example>'."
                    )
                try:
                    full_name, from_email_address, domain = _parse_email_with_name(
                        header_value
                    )
                except PatternNotFoundError:
                    try:
                        from_email_address, domain = _parse_email_only(header_value)
                    except PatternNotFoundError as e:
                        raise ValidationError(
                            f"{case_name}.{mail_config_case_keys.headers}.{header_name.capitalize()}"
                            f"does not match the standard format. E.g., "
                            f"'Jane Doe <jane.doe@localhost.example>'"
                        ) from e
                    else:
                        st_cases[case_name]["from_email_address"] = from_email_address
                        st_cases[case_name]["domain"] = domain
                        st_cases[case_name]["main_params"]["user"] = header_value
                else:
                    st_cases[case_name]["full_name"] = full_name
                    st_cases[case_name]["from_email_address"] = from_email_address
                    st_cases[case_name]["domain"] = domain
                    st_cases[case_name]["main_params"]["user"] = {
                        from_email_address: full_name
                    }
            elif header_name == required_headers_names.to:
                if isinstance(header_value, str) or isinstance(header_value, list):
                    st_cases[case_name]["to"] = []
                    if isinstance(header_value, str):
                        header_value = [header_value]
                    for each_header_value in header_value:
                        try:
                            full_name, to_email_address, domain = (
                                _parse_email_with_name(each_header_value)
                            )
                        except PatternNotFoundError:
                            try:
                                to_email_address, domain = _parse_email_only(
                                    each_header_value
                                )
                            except PatternNotFoundError as e:
                                raise ValidationError(
                                    f"{case_name}.{mail_config_case_keys.headers}.{header_name.capitalize()}"
                                    f"does not match the standard format. E.g., "
                                    f"'Jane Doe <jane.doe@localhost.example>'"
                                ) from e
                            else:
                                st_cases[case_name]["to"].append(each_header_value)
                        else:
                            st_cases[case_name]["to"].append(each_header_value)
                else:
                    raise ValidationError(
                        f"'{case_name}.{mail_config_case_keys.headers}.{header_name.capitalize()}' "
                        f"header must be a string or list of strings. "
                        f"E.g., 'Jane Doe <jane.doe@localhost.example>'."
                    )
            else:
                st_cases[case_name]["headers"][header_name.capitalize()] = header_value
    st_test_case = st_cases.pop(mail_config_sp_keys.case_test, {})
    return st_cases, st_test_case


def get_validated_real_email_cases():
    if _validated_email_cases.real_cases:
        return _validated_email_cases.real_cases
    try:
        real_cases, test_case = get_structured_email_cases()
    except ValidationError as e:
        logger.error(e)
        raise Exit(1)
    else:
        all_cases = {**real_cases, **{mail_config_sp_keys.case_test: test_case}}
        logger.debug("All email cases will be validated.")
        for case_name, case_val in all_cases.items():
            mail_session = yagmail.SMTP(
                **case_val["main_params"], soft_email_validation=False
            )
            mail_session.close()
        _validated_email_cases.real_cases = real_cases
        _validated_email_cases.test_case = test_case
        return _validated_email_cases.real_cases
