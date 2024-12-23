# ruff: noqa: F401
try:
    from .cli import app
except ImportError:
    # Mainly because bill-teams is optional plugin.
    # So, "app" might not be importable unless all necessary dependencies are installed.
    ...
