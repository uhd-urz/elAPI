import yagmail

from ...core_validators import (
    Exit,
)
from ...loggers import Logger
from ...plugins.commons import Typer
from ...utils import GlobalCLICallback, GlobalCLIResultCallback
from .configuration import (
    _validated_email_cases,
    get_mail_is_early_validation_allowed,
    get_validated_real_email_cases,
)
from .names import MailConfigCaseSpecialKeys

app = Typer(name="mail", help="Manage mail.")
logger = Logger()
mail_config_sp_keys = MailConfigCaseSpecialKeys()

GlobalCLIResultCallback().add_callback(
    lambda: print("Dummy processing the stored logs and sending emails.")
)


if get_mail_is_early_validation_allowed() is True:
    GlobalCLICallback().add_callback(get_validated_real_email_cases)


@app.command(name="test", help=f"Send a test email ({mail_config_sp_keys.case_test})")
def test():
    email_test_case = _validated_email_cases.test_case
    if not email_test_case:
        _, email_test_case = get_validated_real_email_cases()
    if not email_test_case:
        logger.error(
            f"No {mail_config_sp_keys.case_test} email case found "
            f"in the configuration file."
        )
        raise Exit(1)
    mail_session = yagmail.SMTP(
        **email_test_case["main_params"], soft_email_validation=False
    )
    logger.info(
        f"Sending a test email to {email_test_case['to']}, "
        f"from {email_test_case['main_params']['user']}, with the "
        f"following headers: {email_test_case['headers']}."
    )
    mail_session.send(
        to=email_test_case["to"],
        contents=email_test_case["body"],
        headers=email_test_case["headers"],
    )
