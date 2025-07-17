import re
from dataclasses import asdict, dataclass
from email.utils import make_msgid
from functools import partial
from logging import LogRecord
from socket import getfqdn
from typing import Iterable, Optional

import jinja2
import yagmail
from nameparser import HumanName

from ... import APP_NAME
from ...loggers import GlobalLogRecordContainer, Logger
from ..commons.cli_helpers import detected_click_feedback
from ._yagmail import YagMailSendParams
from ._yagmail_patch import prepare_enforced_plaintext_message
from .configuration import (
    _validated_email_cases,
    mail_body_jinja_context,
    populate_validated_email_cases,
)
from .names import MailConfigCaseKeys, MailConfigCaseSpecialKeys, MailConfigKeys

mail_config_sp_keys = MailConfigCaseSpecialKeys()
mail_config_case_keys = MailConfigCaseKeys()
mail_config_keys = MailConfigKeys()

logger = Logger()
jinja_environment = jinja2.Environment()


@dataclass
class _IteratingCase:
    target_command: str
    target_log_levels: Iterable[str]
    target_pattern: Optional[str]


def get_case_match() -> Optional[tuple[str, dict, LogRecord]]:
    if not _validated_email_cases.successfully_validated:
        populate_validated_email_cases()
    validated_real_cases = _validated_email_cases.real_cases

    def _debug_matching_case(
        case_name_: str,
        message: str,
        level_name: str,
        target_command_: str,
        target_log_levels: list[str],
        target_pattern: Optional[str],
    ):
        logger.debug(
            f"The log '{message}' with level '{level_name}' matched case "
            f"'{case_name_}' with target levels {target_log_levels}, "
            f"pattern '{target_pattern}', and target command "
            f"'{target_command_}'."
        )

    def _search_match(
        stored_logs: list[LogRecord], cases: dict
    ) -> Optional[tuple[str, dict, LogRecord]]:
        for log_record in stored_logs:
            for case_name_, case_value_ in cases.items():
                iterating_case = _IteratingCase(
                    target_command=case_value.get(mail_config_case_keys.target_command),
                    target_log_levels=list(
                        map(
                            lambda s: s.lower(),
                            case_value_.get(mail_config_case_keys.on, []),
                        )
                    ),
                    target_pattern=case_value_.get(mail_config_case_keys.pattern),
                )
                target_pattern_search = (
                    partial(
                        re.search,
                        pattern=rf"{iterating_case.target_pattern}",
                        flags=re.IGNORECASE,
                    )
                    if iterating_case.target_pattern is not None
                    else lambda string: None
                )
                iterating_log_info = (
                    log_record.levelname.lower(),
                    log_record.message,
                    detected_click_feedback.commands,
                )
                match iterating_log_info:
                    case (
                        level,
                        message,
                        iterating_case.target_command,
                    ) if (
                        level in iterating_case.target_log_levels
                        and target_pattern_search(string=message)
                    ):
                        _debug_matching_case(
                            case_name_,
                            log_record.message,
                            log_record.levelname,
                            *asdict(iterating_case).values(),
                        )
                        return case_name_, case_value_, log_record
                    case (
                        level,
                        _,
                        iterating_case.target_command,
                    ) if level in iterating_case.target_log_levels:
                        _debug_matching_case(
                            case_name_,
                            log_record.message,
                            log_record.levelname,
                            *asdict(iterating_case).values(),
                        )
                        return case_name_, case_value_, log_record
                    case (
                        _,
                        message,
                        iterating_case.target_command,
                    ) if target_pattern_search(string=message):
                        _debug_matching_case(
                            case_name_,
                            log_record.message,
                            log_record.levelname,
                            *asdict(iterating_case).values(),
                        )
                        return case_name_, case_value_, log_record
        return None

    logger.debug(
        f"Detected running {APP_NAME} command/plugin: "
        f"'{detected_click_feedback.commands}'."
    )
    target_command_case_group: dict[str, dict] = {}
    none_command_case_group: dict[str, dict] = {}
    for case_name, case_value in validated_real_cases.items():
        match target_command := case_value.get(mail_config_case_keys.target_command):
            case str():
                target_command: str = re.sub(
                    rf"^{APP_NAME} ?", "", target_command, re.IGNORECASE
                ).strip()
        match target_command:
            case detected_click_feedback.commands:
                target_command_case_group[case_name] = case_value
            case None:
                case_value[mail_config_case_keys.target_command] = (
                    detected_click_feedback.commands
                )
                none_command_case_group[case_name] = case_value

    if target_command_case_group:
        return _search_match(
            GlobalLogRecordContainer().data,
            {**target_command_case_group, **none_command_case_group},
        )
    return _search_match(
        GlobalLogRecordContainer().data,
        none_command_case_group,
    )


def _get_clean_logs(log_records: list[LogRecord]) -> str:
    messages: list[str] = []
    for record in log_records:
        messages.append(f"{record.asctime}:{record.levelname}: {record.message}")
    return "\n".join(messages)


def _process_jinja_context(case_value: dict):
    mail_body_jinja_context["all_logs"] = _get_clean_logs(
        GlobalLogRecordContainer().data
    )
    mail_body_jinja_context["sender_full_name"] = case_value.get("sender_full_name", "")
    mail_body_jinja_context["server_fqdn"] = getfqdn()
    mail_body_jinja_context["unique_receiver_full_name"] = receiver_full_name = (
        case_value.get("receiver_full_name", "")
    )
    mail_body_jinja_context["unique_receiver_first_name"] = receiver_first_name = (
        HumanName(receiver_full_name).first
    )
    mail_body_jinja_context["unique_receiver_name"] = (
        receiver_first_name or receiver_full_name
    )


def send_matching_case_mail() -> None:
    matching_case: Optional[tuple[str, dict, LogRecord]] = get_case_match()
    if matching_case is None:
        logger.debug(
            f"No log was found that matches any case defined in "
            f"'{mail_config_keys.plugin_name}.{mail_config_keys.cases}'."
        )
        return
    case_name, case_value, log_record = matching_case
    _process_jinja_context(case_value)
    logger.info(
        f"A log was found that matches the case '{case_name}' defined in "
        f"{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
    )
    _send_yagmail(case_name, case_value, jinja_contex=mail_body_jinja_context)
    GlobalLogRecordContainer().data.clear()
    logger.debug(f"{GlobalLogRecordContainer} data has been cleared.")


def _send_yagmail(
    case_name: str, case_value: dict, jinja_contex: Optional[dict] = None
) -> None:
    mail_session = yagmail.SMTP(
        **case_value["main_params"], soft_email_validation=False
    )
    email_body_template = jinja_environment.from_string(case_value["body"])
    email_body: str = email_body_template.render(jinja_contex or dict())
    yagmail_send_params = YagMailSendParams(
        to=case_value["to"],
        contents=email_body,
        headers=case_value["headers"],
        message_id=make_msgid(domain=case_value["sender_domain"]),
    )
    if case_value[mail_config_case_keys.enforce_plaintext_email] is True:
        logger.debug(
            f"'{mail_config_case_keys.enforce_plaintext_email}' "
            f"is enabled for mail case '{case_name}'."
        )
        yagmail.message.prepare_message = prepare_enforced_plaintext_message
        yagmail.sender.prepare_message = prepare_enforced_plaintext_message
        yagmail_send_params.prettify_html = False
    logger.info(
        f"Attempting to send a '{case_name}' email to "
        f"'{', '.join(case_value['to'])}',\n"
        f"from '{''.join(case_value['main_params']['user'].keys())}',"
        f"\nwith the "
        f"following additional headers: {case_value['headers']}."
    )
    mail_session.send(**yagmail_send_params.__dict__)
    mail_session.close()
