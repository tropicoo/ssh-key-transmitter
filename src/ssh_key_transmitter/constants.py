from typing import Final
from importlib.metadata import version as metadata_version

PKG_NAME: Final[str] = 'ssh-key-transmitter'
APP_NAME: Final[str] = 'SSH Key Transmitter'
APP_VERSION: Final[str] = metadata_version(PKG_NAME)

DEFAULT_SSH_PORT: Final[int] = 22
DEFAULT_SSH_DIR: Final[str] = '.ssh'
DEFAULT_SSH_AUTH_KEYS: Final[str] = 'authorized_keys'
