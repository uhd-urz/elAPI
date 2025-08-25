from importlib.util import find_spec

if not (find_spec("yagmail") and find_spec("jinja2") and find_spec("nameparser")):
    ...
else:
    from ...core_validators import Exit
    from ...loggers import Logger, ResultCallbackHandler
    from ...plugins.commons import Typer
    from ...utils import GlobalCLIGracefulCallback, GlobalCLIResultCallback
    from .configuration import (
        _validated_email_cases,
        get_mail_is_early_validation_allowed,
        mail_body_jinja_context,
        populate_validated_email_cases,
    )
    from .mail import process_jinja_context, send_mail, send_matching_case_mail
    from .names import mail_config_sp_keys

    app = Typer(name="mail", help="Manage mail.")
    ResultCallbackHandler.enable_store_okay()
    logger = Logger()

    GlobalCLIResultCallback().add_callback(send_matching_case_mail)

    if get_mail_is_early_validation_allowed() is True:
        GlobalCLIGracefulCallback().add_callback(populate_validated_email_cases)

    @app.command(
        name="test",
        help=f"Send a test email ({mail_config_sp_keys.case_test})",
    )
    def test():
        if not _validated_email_cases.successfully_validated:
            populate_validated_email_cases()
        email_test_case = _validated_email_cases.test_case
        if not email_test_case:
            logger.error(
                f"No non-empty '{mail_config_sp_keys.case_test}' "
                f"email case found in the configuration file."
            )
            raise Exit(1)
        process_jinja_context(email_test_case)
        send_mail(
            case_name=mail_config_sp_keys.case_test,
            case_value=email_test_case,
            jinja_contex=mail_body_jinja_context,
        )
