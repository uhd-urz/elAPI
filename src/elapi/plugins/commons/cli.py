from ...configuration import get_development_mode
from ...utils import GlobalCLIGracefulCallback
from .get_whoami import debug_log_whoami_message

if get_development_mode(skip_validation=True):
    GlobalCLIGracefulCallback().add_callback(debug_log_whoami_message)
