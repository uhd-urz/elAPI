import re
from email.utils import make_msgid
from logging import LogRecord
from typing import Optional

import yagmail

from ...loggers import GlobalLogRecordContainer, Logger
from ._yagmail import YagMailSendParams
from .configuration import _validated_email_cases, populate_validated_email_cases
from .names import MailConfigCaseKeys, MailConfigCaseSpecialKeys, MailConfigKeys

mail_config_sp_keys = MailConfigCaseSpecialKeys()
mail_config_case_keys = MailConfigCaseKeys()
mail_config_keys = MailConfigKeys()

logger = Logger()


def get_case_match() -> Optional[tuple[str, dict, LogRecord]]:
    if not _validated_email_cases.successfully_validated:
        populate_validated_email_cases()
    validated_real_cases = _validated_email_cases.real_cases
    stored_logs: list[LogRecord] = GlobalLogRecordContainer().data
    for log_record in stored_logs:
        for case_name, case_value in validated_real_cases.items():
            target_log_levels: list[str] = (
                case_value.get(mail_config_case_keys.on) or []
            )
            target_log_levels = [_.lower() for _ in target_log_levels]
            target_pattern: str = case_value.get(mail_config_case_keys.pattern) or ""
            if target_log_levels and target_pattern:
                if log_record.levelname.lower() in target_log_levels and re.search(
                    rf"{target_pattern}", log_record.message, re.IGNORECASE
                ):
                    return case_name, case_value, log_record
            elif target_log_levels:
                if log_record.levelname.lower() in target_log_levels:
                    return case_name, case_value, log_record
            elif target_pattern:
                if re.search(rf"{target_pattern}", log_record.message, re.IGNORECASE):
                    return case_name, case_value, log_record
    return None


def send_matching_case_mail() -> None:
    matching_case: Optional[tuple[str, dict, LogRecord]] = get_case_match()
    if matching_case is None:
        logger.debug(
            f"No log was found that matches any case defined in "
            f"{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
        )
        return
    case_name, case_value, log_record = matching_case
    logger.info(
        f"A log was found that matches the case '{case_name}' defined in "
        f"{mail_config_keys.plugin_name}.{mail_config_keys.cases}."
    )
    _send_yagmail(case_name, case_value)
    GlobalLogRecordContainer().data.clear()
    logger.debug(f"{GlobalLogRecordContainer} data has been cleared.")


def _send_yagmail(case_name: str, case_value: dict) -> None:
    mail_session = yagmail.SMTP(
        **case_value["main_params"], soft_email_validation=False
    )
    yagmail_send_params = YagMailSendParams(
        to=case_value["to"],
        contents=case_value["body"],
        headers=case_value["headers"],
        message_id=make_msgid(domain=case_value["domain"]),
    )
    logger.info(
        f"Attempting to send a '{case_name}' email to "
        f"'{', '.join(case_value['to'])}',\n"
        f"from '{''.join(case_value['main_params']['user'].keys())}',"
        f"\nwith the "
        f"following headers: {case_value['headers']}."
    )
    mail_session.send(**yagmail_send_params.__dict__)
    mail_session.close()
