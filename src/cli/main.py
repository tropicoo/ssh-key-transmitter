from pathlib import Path
from typing import Annotated

from rich import print as rich_print
from typer import Abort, Option

from src.cli.callbacks import typer_version_callback
from src.core.manager import SocksManager
from src.core.transmitter import SSHKeyTransmitter
from src.enums import ExitCodeType, LogLevelType
from src.log import init_logging


def main(
    username: Annotated[
        str,
        Option(
            '-u',
            '--username',
            show_default=False,
            help='auth username',
        ),
    ],
    password: Annotated[
        str,
        Option(
            '-p',
            '--password',
            show_default=False,
            help='auth password',
        ),
    ],
    pubkey: Annotated[
        Path,
        Option(
            '-pk',
            '--pub-key',
            exists=True,
            file_okay=True,
            dir_okay=False,
            show_default=False,
            help='path to public key file',
        ),
    ],
    socks_host: Annotated[
        str | None,
        Option(
            '--socks-host',
            show_default=False,
            help='socks5 proxy host',
        ),
    ] = None,
    socks_port: Annotated[
        int | None,
        Option(
            '--socks-port',
            show_default=False,
            help='socks5 proxy port',
        ),
    ] = None,
    hosts_file: Annotated[
        Path | None,
        Option(
            '--hosts-file',
            exists=True,
            file_okay=True,
            dir_okay=False,
            show_default=False,
            help='path to file with hosts list',
        ),
    ] = None,
    hosts: Annotated[
        list[str] | None,
        Option(
            '-hosts',
            show_default=False,
            help='host(s) to transmit ssh public key',
        ),
    ] = None,
    verbose: Annotated[
        int,
        Option(
            '-v',
            '--verbose',
            min=LogLevelType.ERROR,
            max=LogLevelType.DEBUG,
            help='log level 0-3. Default 2 (INFO)',
        ),
    ] = LogLevelType.INFO,
    version: Annotated[  # noqa: ARG001, FBT002
        bool,
        Option(
            '-V',
            '--version',
            callback=typer_version_callback,
            help='show application version',
        ),
    ] = False,
) -> ExitCodeType:
    """SSH Key Transmitter."""
    if not any((hosts, hosts_file)):
        rich_print('[bold red]Provide host(s) or path to hosts file.[/bold red]')
        raise Abort

    init_logging(level=LogLevelType(verbose))

    transmitter = SSHKeyTransmitter(
        username=username,
        password=password,
        pubkey=pubkey,
        hosts=hosts,
        hosts_file=hosts_file,
        socks_manager=SocksManager(
            socks_host=socks_host,
            socks_port=socks_port,
        ),
    )
    transmitter.run()
    return ExitCodeType.EXIT_OK
