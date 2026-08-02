"""SSH Key Transmitter Module."""

import typer

from ssh_key_transmitter.cli.cli_main import cli_main_entrypoint


def main() -> None:
    typer.run(cli_main_entrypoint)
