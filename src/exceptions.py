class SSHKeyTransmitterError(Exception):
    """SSH Key Transmitter Base Exception Class."""


class DataReadError(SSHKeyTransmitterError):
    """SSH Key Transmitter Data Read Exception Class.

    Used for local files read errors.
    """
