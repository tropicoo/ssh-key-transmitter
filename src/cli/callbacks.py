from typer import Exit

from src.constants import APP_NAME
from src.enums import ExitCodeType
from src.version import __version__


def typer_version_callback(value: bool) -> None:  # noqa: FBT001
    if value:
        print(f'{APP_NAME} Version: {__version__}')  # noqa: T201
        raise Exit(code=ExitCodeType.EXIT_OK)
