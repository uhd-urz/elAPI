import re
from collections import UserDict
from dataclasses import asdict, dataclass
from typing import Any

from yagmail.validate import DOMAIN, LOCAL_PART

from ... import APP_NAME
from ...configuration import (
    get_active_plugin_configs,
)
from ...core_validators import Exit, ValidationError
from ...loggers import Logger
from ...path import ProperPath
from ...styles import Missing
from ...utils import PatternNotFoundError
from .names import (
    mail_config_case_keys,
    mail_config_default_values,
    mail_config_keys,
    mail_config_sp_keys,
)
from .yagmail_configuration import (
    _get_formatted_fallback_from_email_address,
    get_additional_yagmail_smtp_class_params,
    main_email_setting_fallback_values,
    main_email_setting_params,
    required_email_headers_fallback_params,
    required_email_headers_params,
    yagmail_smtp_unused_params,
)

logger = Logger()


class MailBodyJinjaContext(UserDict):
    def __init__(self):
        self.reserved_keys = (
            "all_logs",
            "sender_full_name",
            "unique_receiver_full_name",
            "unique_receiver_first_name",
            "unique_receiver_name",
            "server_fqdn",
        )
        super().__init__({k: None for k in self.reserved_keys})

    def __delitem__(self, key):
        if key in self.reserved_keys:
            raise ValueError(f"Key '{key}' is reserved and cannot be deleted.")
        self.data.pop(key, None)


mail_body_jinja_context = MailBodyJinjaContext()


@dataclass
class _ValidatedEmailCases:
    real_cases: dict
    test_case: dict
    successfully_validated: bool


_validated_email_cases = _ValidatedEmailCases(
    real_cases=dict(), test_case=dict(), successfully_validated=False
)


def get_mail_config() -> dict:
    plugin_configs = get_active_plugin_configs(skip_validation=True)
    if plugin_configs == Missing():
        return mail_config_default_values.plugin_name
    return (
        get_active_plugin_configs().get(
            mail_config_keys.plugin_name,
            mail_config_default_values.plugin_name,
        )
        or dict()
    )


def get_mail_is_early_validation_allowed() -> bool:
    return get_mail_config().get(
        mail_config_keys.validate_config_early,
        mail_config_default_values.validate_config_early,
    )


def get_global_email_setting() -> dict:
    return (
        get_mail_config().get(
            mail_config_keys.global_email_setting,
            mail_config_default_values.global_email_setting,
        )
        or dict()
    )


def get_global_email_headers() -> dict:
    return (
        get_mail_config().get(
            mail_config_keys.global_email_headers,
            mail_config_default_values.global_email_headers,
        )
        or dict()
    )


def get_email_cases() -> dict:
    return (
        get_mail_config().get(
            mail_config_keys.cases,
            mail_config_default_values.cases,
        )
        or dict()
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
    def _get_preferred_case_value(
        local_value: Any, global_value: Any, default_value: Any = None
    ) -> Any:
        if local_value is not None:
            return local_value
        if global_value is not None:
            return global_value
        return default_value

    global_email_setting: dict = get_global_email_setting()
    st_cases: dict = {}
    for case_name, case_val in get_email_cases().items():
        st_cases[case_name] = {}
        case_on = case_val.get(mail_config_case_keys.on)
        case_pattern = case_val.get(mail_config_case_keys.pattern)
        case_target_command = case_val.get(mail_config_case_keys.target_command)
        if case_on is None and case_pattern is None:
            if case_name != mail_config_sp_keys.case_test:
                raise ValidationError(
                    f"Either '{mail_config_case_keys.on}' or "
                    f"'{mail_config_case_keys.pattern}' "
                    f"or both must be provided for case '{mail_config_keys.plugin_name}."
                    f"{mail_config_keys.cases}.{case_name}'."
                )
        if case_on is not None:
            if case_name == mail_config_sp_keys.case_test:
                logger.info(
                    f"Email case '{case_name}' is special, and "
                    f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                    f"{case_name}.{mail_config_case_keys.on}' will be ignored."
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
                    f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                    f"{case_name}.{mail_config_case_keys.pattern}' will be ignored."
                )
            elif not isinstance(case_pattern, str):
                raise ValidationError(
                    f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                    f"{case_name}.{mail_config_case_keys.pattern}' must be a string of "
                    f"Python regex pattern."
                )
            st_cases[case_name][mail_config_case_keys.pattern] = case_pattern
        if case_target_command is not None:
            if case_name == mail_config_sp_keys.case_test:
                logger.info(
                    f"Email case '{case_name}' is special, and "
                    f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                    f"{case_name}.{mail_config_case_keys.target_command}' will be ignored."
                )
            elif not isinstance(case_target_command, str):
                raise ValidationError(
                    f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                    f"{case_name}.{mail_config_case_keys.target_command}' must be a string of "
                    f"explicit {APP_NAME} command. E.g., 'experiments get', "
                    f"'bill-teams registry include'."
                )
            st_cases[case_name][mail_config_case_keys.target_command] = (
                case_target_command
            )
        case_body = case_val.get(mail_config_case_keys.body)
        if case_body is None:
            case_body: str = ""
            st_cases[case_name][mail_config_case_keys.body] = case_body
        else:
            try:
                case_body_path = ProperPath(case_body)
            except ValueError as e:
                raise ValidationError(
                    f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                    f"{case_name}.{mail_config_case_keys.body}' "
                    f"value '{case_body}' is an invalid path value."
                ) from e
            else:
                if (
                    not case_body_path.kind == "file"
                    or not case_body_path.expanded.exists()
                ):
                    raise ValidationError(
                        f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                        f"{case_name}.{mail_config_case_keys.body}' "
                        f"value '{case_body_path}' is not a file path or "
                        f"does not exist."
                    )
                case_body: str = case_body_path.expanded.read_text()
                st_cases[case_name][mail_config_case_keys.body] = case_body
        st_cases[case_name]["main_params"] = {}
        for required_param in main_email_setting_params.__dict__.values():
            required_param_value = _get_preferred_case_value(
                case_val.get(required_param), global_email_setting.get(required_param)
            )
            if required_param_value is None:
                if (
                    required_param
                    in (
                        default_email_setting_params_dict := asdict(
                            main_email_setting_fallback_values
                        )
                    ).keys()
                ):
                    logger.debug(
                        f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                        f"{case_name}.{required_param}' value is not set (or null), "
                        f"the default (fallback) value "
                        f"'{default_email_setting_params_dict[required_param]}' will be used."
                    )
                    st_cases[case_name]["main_params"][required_param] = (
                        default_email_setting_params_dict[required_param]
                    )
            else:
                st_cases[case_name]["main_params"][required_param] = (
                    required_param_value
                )

        case_enforce_plaintext_email = _get_preferred_case_value(
            case_val.get(mail_config_case_keys.enforce_plaintext_email),
            global_email_setting.get(mail_config_case_keys.enforce_plaintext_email),
            default_value=False,
        )
        if not isinstance(case_enforce_plaintext_email, bool):
            raise ValidationError(
                f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                f"{case_name}.{mail_config_case_keys.enforce_plaintext_email}' "
                f"value must be boolean."
            )
        st_cases[case_name][mail_config_case_keys.enforce_plaintext_email] = (
            case_enforce_plaintext_email
        )
        for additional_param in get_additional_yagmail_smtp_class_params():
            additional_param_value = _get_preferred_case_value(
                case_val.get(additional_param),
                global_email_setting.get(additional_param),
            )
            if additional_param_value is not None:
                st_cases[case_name]["main_params"][additional_param] = (
                    additional_param_value
                )
        for unused_param in yagmail_smtp_unused_params.__dict__.values():
            unused_param_value = _get_preferred_case_value(
                case_val.get(unused_param),
                global_email_setting.get(unused_param),
            )
            if unused_param_value is not None:
                raise ValidationError(
                    f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
                    f"{case_name}.{unused_param}' cannot be used in this context."
                )
        case_headers = case_val.get(mail_config_case_keys.headers, dict())
        case_headers_lower = {k.lower(): v for k, v in case_headers.items()}
        global_email_headers_lower = {
            k.lower(): v for k, v in get_global_email_headers().items()
        }
        st_cases[case_name]["headers"] = {}
        unique_header_names: set[str] = {
            *case_headers_lower.keys(),
            *global_email_headers_lower.keys(),
        }
        for header_name in (
            unique_header_names
            | set(asdict(required_email_headers_params).values())
            | set(asdict(required_email_headers_fallback_params).values())
        ):
            header_value = _get_preferred_case_value(
                case_headers_lower.get(header_name),
                global_email_headers_lower.get(header_name),
            )
            if header_value is None:
                if header_name in asdict(required_email_headers_params).values():
                    raise ValidationError(
                        f"'{case_name}.{mail_config_case_keys.headers}."
                        f"{header_name.capitalize()}' header must be provided."
                    )
            if header_name == required_email_headers_fallback_params.From:
                if header_value is None:
                    if (
                        header_value := _get_formatted_fallback_from_email_address()
                    ) is None:
                        raise ValidationError(
                            f"A fallback value for '{case_name}.{mail_config_case_keys.headers}."
                            f"{header_name.capitalize()}' header could not be used, "
                            f"so a valid header value must must be provided in configuration file!"
                        )
                    else:
                        logger.debug(
                            f"'{case_name}.{mail_config_case_keys.headers}."
                            f"{header_name.capitalize()}' header value is empty or null. A fallback value "
                            f"'{header_value}' will be used."
                        )
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
                            f"'{case_name}.{mail_config_case_keys.headers}.{header_name.capitalize()}' value "
                            f"'{header_value}' does not match the standard format. E.g., "
                            f"'Jane Doe <jane.doe@localhost.example>'."
                        ) from e
                    else:
                        st_cases[case_name]["from_email_address"] = from_email_address
                        st_cases[case_name]["sender_domain"] = domain
                        st_cases[case_name]["main_params"]["user"] = header_value
                else:
                    st_cases[case_name]["sender_full_name"] = full_name
                    st_cases[case_name]["from_email_address"] = from_email_address
                    st_cases[case_name]["sender_domain"] = domain
                    st_cases[case_name]["main_params"]["user"] = {
                        from_email_address: full_name
                    }
            elif header_name == required_email_headers_params.To:
                if isinstance(header_value, str) or isinstance(header_value, list):
                    st_cases[case_name][required_email_headers_params.To] = []
                    if isinstance(header_value, str):
                        header_value = [header_value]
                    for each_header_value in header_value:
                        try:
                            full_name, _to_email_address, _domain = (
                                _parse_email_with_name(each_header_value)
                            )
                        except PatternNotFoundError:
                            try:
                                _to_email_address, _domain = _parse_email_only(
                                    each_header_value
                                )
                            except PatternNotFoundError as e:
                                raise ValidationError(
                                    f"'{case_name}.{mail_config_case_keys.headers}.{header_name.capitalize()}' "
                                    f"does not match the standard format. E.g., "
                                    f"'Jane Doe <jane.doe@localhost.example>'"
                                ) from e
                            else:
                                st_cases[case_name][
                                    required_email_headers_params.To
                                ].append(each_header_value)
                        else:
                            try:
                                st_cases[case_name]["receiver_full_name"]
                            except KeyError:
                                st_cases[case_name]["receiver_full_name"] = full_name
                            else:
                                st_cases[case_name].pop("receiver_full_name")
                            st_cases[case_name][
                                required_email_headers_params.To
                            ].append(each_header_value)
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


def populate_validated_email_cases() -> None:
    if _validated_email_cases.successfully_validated:
        return None
    try:
        logger.debug("Email cases are to be validated.")
        real_cases, test_case = get_structured_email_cases()
    except ValidationError as e:
        logger.error(e)
        raise Exit(1)
    else:
        if not real_cases or not test_case:
            logger.debug(
                "No real email cases or test case were found. Nothing to validate."
            )
            return None
        _validated_email_cases.successfully_validated = True
        _validated_email_cases.real_cases = real_cases
        _validated_email_cases.test_case = test_case
