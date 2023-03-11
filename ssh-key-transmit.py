#!/usr/bin/env python3
"""SSH Key Transmitter Module."""

import argparse
import logging
import posixpath
import sys
from typing import List, Optional, Union

import paramiko
import socks
from paramiko.sftp_client import SFTPClient

__version__ = '0.2.1'

BANNER_TPL = """


███████╗███████╗██╗  ██╗    ██╗  ██╗███████╗██╗   ██╗    ████████╗██████╗  █████╗ ███╗   ██╗███████╗███╗   ███╗██╗████████╗████████╗███████╗██████╗
██╔════╝██╔════╝██║  ██║    ██║ ██╔╝██╔════╝╚██╗ ██╔╝    ╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝████╗ ████║██║╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗
███████╗███████╗███████║    █████╔╝ █████╗   ╚████╔╝        ██║   ██████╔╝███████║██╔██╗ ██║███████╗██╔████╔██║██║   ██║      ██║   █████╗  ██████╔╝
╚════██║╚════██║██╔══██║    ██╔═██╗ ██╔══╝    ╚██╔╝         ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██║╚██╔╝██║██║   ██║      ██║   ██╔══╝  ██╔══██╗
███████║███████║██║  ██║    ██║  ██╗███████╗   ██║          ██║   ██║  ██║██║  ██║██║ ╚████║███████║██║ ╚═╝ ██║██║   ██║      ██║   ███████╗██║  ██║
╚══════╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝   ╚═╝          ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚═╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝
                                                                                                                                          ver. {version}

"""
SSH_PORT = 22
SSH_DIR = '.ssh'
SSH_AUTH_KEYS = 'authorized_keys'

EXIT_OK = 0
EXIT_ERROR = 1


class SSHKeyTransmitterError(Exception):
    """SSH Key Transmitter Base Exception Class."""

    pass


class DataReadError(SSHKeyTransmitterError):
    """SSH Key Transmitter Data Read Exception Class.

    Used for local files read errors.
    """

    pass


class ArgumentsValidationError(Exception):
    pass


class SocksManager:
    """Socks manager class."""

    def __init__(self, socks_host: str, socks_port: int) -> None:
        """Constructor.

        :Parameters:
            - `socks_host`: str, SOCKS5 proxy host.
            - `socks_port`: str, SOCKS5 proxy port.
        """
        self._host = socks_host
        self._port = socks_port

    def create_socket(
            self, dest_host: str, dest_port: Union[str, int]
    ) -> Optional[socks.socksocket]:
        """Create open socket.

        :Parameters:
            - `dest_host`: str, destination host to connect through proxy.
            - `dest_port`: str/int, destination port to connect through proxy.
        """
        if not (self._host and self._port):
            return None
        sock = socks.socksocket()
        sock.set_proxy(proxy_type=socks.SOCKS5, addr=self._host, port=self._port)
        sock.connect((dest_host, dest_port))
        return sock


class SSHKeyTransmitter:
    """SSH Key Transmitter Class."""

    def __init__(
            self,
            username: str,
            password: str,
            pubkey: str,
            socks_manager: SocksManager,
            hosts: Optional[List[str]] = None,
            hosts_file: Optional[str] = None,
    ) -> None:
        """Constructor.

        :Parameters:
            - `username`: str, auth username.
            - `password`: str, auth password.
            - `hosts`: list, hosts list to transmit.
            - `hosts_file`: str, path to file with hosts to transmit.
            - `pubkey`: str, path to public key file.
            - `socks_manager`: obj, Socks manager instance.
        """
        self._log = logging.getLogger(self.__class__.__name__)

        self._username = username
        self._password = password
        self._hosts = set(hosts) if hosts else set()
        self._hosts_file = hosts_file
        self._pubkey_file = pubkey
        self._pubkey_data = None

        self._socks_manager = socks_manager

        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def run(self) -> int:
        """Run SSH Key Transmitter.

        Return
            - Int value indicating if transmit failed on any host.
        """
        exit_code = EXIT_OK

        if not self._pubkey_file:
            self._log.error('Path to public key not provided. Cannot proceed.')
            return EXIT_ERROR

        try:
            self._read_data()
        except DataReadError:
            return EXIT_ERROR

        errored_hosts = self._run()
        if errored_hosts:
            exit_code = EXIT_ERROR
            self._log.warning('Errored hosts: %s', ', '.join(errored_hosts))

        self._log.info(
            'Finished transmitting %s [exit code: %s]', self._pubkey_file, exit_code
        )
        return exit_code

    def _run(self) -> List[str]:
        """Main transmit."""
        errored_hosts = []
        for host in self._hosts:
            try:
                host, port = host.split(':')
            except ValueError:
                port = SSH_PORT

            self._log.info('Transmitting public key to %s:%s', host, port)
            sock = None
            try:
                sock = self._socks_manager.create_socket(host, port)
                self._ssh.connect(
                    hostname=host,
                    port=port,
                    username=self._username,
                    password=self._password,
                    sock=sock,
                )
                self._put_public_key()
            except SSHKeyTransmitterError:
                errored_hosts.append(host)
            except paramiko.ssh_exception.AuthenticationException as err:
                self._log.error('Failed to authenticate to %s: %s', host, err)
                errored_hosts.append(host)
            except Exception:
                self._log.exception('Failed to transmit SSH files to %s', host)
                errored_hosts.append(host)
            finally:
                self._cleanup(sock)
        return errored_hosts

    def _read_data(self) -> None:
        """Read public key and hosts file."""
        self._read_pubkey()
        if self._hosts_file:
            self._read_hosts_from_file()

    def _cleanup(self, sock) -> None:
        """Transmitter cleanup."""
        if self._ssh.get_transport():
            self._ssh.close()
        if sock:
            sock.close()

    def _put_public_key(self) -> None:
        """Transmit public key to connected host."""
        sftp = self._ssh.open_sftp()
        try:
            # Throw IOError if directory doesn't exist
            sftp.chdir(SSH_DIR)
        except IOError:
            sftp.chdir('.')
            self._log.warning(
                'Directory %s does not exist. Will be created.',
                posixpath.join(sftp.getcwd(), SSH_DIR),
            )
            self._create_ssh_dir(sftp)

        try:
            self._put_key(sftp)
        finally:
            sftp.close()

    @staticmethod
    def _create_ssh_dir(sftp: SFTPClient) -> None:
        """Create `SSH_DIR` directory.

        :Parameters:
            - `sftp`: obj, paramiko sftp object.
        """
        sftp.mkdir(SSH_DIR)
        sftp.chmod(SSH_DIR, 0o700)
        sftp.chdir(SSH_DIR)

    def _put_key(self, sftp: SFTPClient) -> None:
        """Transmit public key to connected host.

        :Parameters:
            - `sftp`: obj, paramiko sftp object.
        """
        remote_path = posixpath.join(sftp.getcwd(), SSH_AUTH_KEYS)
        try:
            # Throw IOError if file doesn't exist
            sftp.stat(SSH_AUTH_KEYS)
        except IOError:
            # Create `SSH_AUTH_KEYS` file
            self._log.warning('File %s does not exist. Will be created.', remote_path)
            self._create_ssh_auth_keys_file(sftp, remote_path)
            self._log.info(
                'Public key %s successfully added to %s', self._pubkey_file, remote_path
            )
            return

        if not self._key_exists(sftp, remote_path):
            self._append_key(sftp, remote_path)

    def _create_ssh_auth_keys_file(self, sftp: SFTPClient, remote_path: str) -> None:
        """Create `SSH_AUTH_KEYS` file.

        :Parameters:
            - `sftp`: obj, paramiko sftp object.
            - `remote_path`: str, remote path to key.
        """
        sftp.put(self._pubkey_file, remote_path)
        sftp.chmod(remote_path, 0o600)

    def _key_exists(self, sftp: SFTPClient, remote_path: str) -> bool:
        """Check if key exists.

        :Parameters:
            - `sftp`: obj, paramiko sftp object.
            - `remote_path`: str, remote path to key.
        """
        fd = sftp.file(SSH_AUTH_KEYS, mode='r', bufsize=1)
        try:
            for line in fd:
                if line.strip() == self._pubkey_data:
                    self._log.warning(
                        'Public key %s already exists in %s',
                        self._pubkey_file,
                        remote_path,
                    )
                    return True
        finally:
            fd.close()
        return False

    def _append_key(self, sftp: SFTPClient, remote_path: str) -> None:
        """Append key.

        :Parameters:
            - `sftp`: obj, paramiko sftp object.
            - `remote_path`: str, remote path to key.
        """
        fd = sftp.file(SSH_AUTH_KEYS, mode='a', bufsize=1)
        try:
            fd.write('\n' + self._pubkey_data)
            fd.flush()
        finally:
            fd.close()
        self._log.info(
            'Public key %s successfully appended to %s', self._pubkey_file, remote_path
        )

    def _read_pubkey(self) -> None:
        """Read public key from file."""
        self._log.info('Reading public key from %s', self._pubkey_file)
        try:
            with open(self._pubkey_file, 'r') as fd:
                self._pubkey_data = fd.read().strip()
        except Exception:
            err_msg = 'Failed to read public key from {0}'.format(self._pubkey_file)
            self._log.exception(err_msg)
            raise DataReadError(err_msg)

    def _read_hosts_from_file(self) -> None:
        """Read hosts list from file."""
        self._log.info('Reading hosts list from %s', self._hosts_file)
        try:
            with open(self._hosts_file, 'r') as fd:
                self._hosts.update(fd.read().split())
        except Exception:
            err_msg = 'Failed to read hosts from {0}'.format(self._hosts_file)
            self._log.exception(err_msg)
            raise DataReadError(err_msg)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='SSH Key Transmitter')
    parser.add_argument(
        '-hosts', default=None, nargs='+', help='host(s) to transmit ssh public key'
    )
    parser.add_argument(
        '-u',
        '--username',
        action='store',
        default=None,
        dest='username',
        help='auth username',
    )
    parser.add_argument(
        '-p',
        '--password',
        action='store',
        default=None,
        dest='password',
        help='auth password',
    )
    parser.add_argument(
        '-pkey',
        '--pub-key',
        action='store',
        default=None,
        dest='pubkey',
        help='path to public key',
    )
    parser.add_argument(
        '--hosts-file',
        action='store',
        default=None,
        dest='hosts_file',
        help='path to file with hosts list',
    )
    parser.add_argument(
        '--socks-host',
        action='store',
        default=None,
        dest='socks_host',
        help='socks5 proxy host',
    )
    parser.add_argument(
        '--socks-port',
        action='store',
        default=None,
        dest='socks_port',
        help='socks5 proxy port',
    )
    args = parser.parse_args()

    if not (
            all([args.pubkey, args.username, args.password])
            or any([args.hosts, args.hosts_file])
    ):
        parser.print_help()
        raise ArgumentsValidationError('Failed to parse args')

    return args


def _init_logging() -> None:
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)
    logging.getLogger('paramiko').setLevel(logging.WARNING)


def main() -> int:
    """Main function."""
    print(BANNER_TPL.format(version=__version__))
    _init_logging()
    logger = logging.getLogger(__name__)

    try:
        args = _parse_args()
    except ArgumentsValidationError as err:
        logger.error(err)
        return EXIT_ERROR

    socks_manager = SocksManager(socks_host=args.socks_host, socks_port=args.socks_port)

    transmitter = SSHKeyTransmitter(
        username=args.username,
        password=args.password,
        pubkey=args.pubkey,
        hosts=args.hosts,
        hosts_file=args.hosts_file,
        socks_manager=socks_manager,
    )
    return transmitter.run()


if __name__ == '__main__':
    sys.exit(main())
