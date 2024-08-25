from rich.console import Console

__PACKAGE_IDENTIFIER__: str = __package__
stdin_console = Console(color_system="auto")
stderr_console = Console(color_system="auto", stderr=True)
