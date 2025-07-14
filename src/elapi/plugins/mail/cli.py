from ...core_validators import Exit
from ...loggers import Logger, ResultCallbackHandler
from ...plugins.commons import Typer
from ...utils import GlobalCLIGracefulCallback, GlobalCLIResultCallback
from .configuration import (
    _validated_email_cases,
    get_mail_is_early_validation_allowed,
    get_validated_real_email_cases,
)
from .mail import _send_yagmail, send_matching_case_mail
from .names import MailConfigCaseKeys, MailConfigCaseSpecialKeys, MailConfigKeys

app = Typer(name="mail", help="Manage mail.")
ResultCallbackHandler.enable_store_okay()
logger = Logger()
mail_config_sp_keys = MailConfigCaseSpecialKeys()
mail_config_case_keys = MailConfigCaseKeys()
mail_config_keys = MailConfigKeys()

GlobalCLIResultCallback().add_callback(send_matching_case_mail)


if get_mail_is_early_validation_allowed() is True:
    GlobalCLIGracefulCallback().add_callback(get_validated_real_email_cases)


@app.command(
    name="test",
    help=f"Send a test email ({mail_config_sp_keys.case_test})",
)
def test():
    email_test_case = _validated_email_cases.test_case
    if not email_test_case:
        validated_cases = get_validated_real_email_cases()
        if validated_cases:
            _, email_test_case = validated_cases
    if not email_test_case:
        logger.error(
            f"No non-empty '{mail_config_sp_keys.case_test}' "
            f"email case found in the configuration file."
        )
        raise Exit(1)
    _send_yagmail(
        case_name=mail_config_sp_keys.case_test,
        case_value=email_test_case,
    )
