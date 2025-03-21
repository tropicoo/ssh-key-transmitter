import logging
import posixpath
from pathlib import Path

import socks
from paramiko import AuthenticationException, AutoAddPolicy, SSHClient
from paramiko.sftp_client import SFTPClient

from src.constants import DEFAULT_SSH_AUTH_KEYS, DEFAULT_SSH_DIR, DEFAULT_SSH_PORT
from src.core.manager import SocksManager
from src.exceptions import DataReadError, SSHKeyTransmitterError


class SSHKeyTransmitter:
    """SSH Key Transmitter Class."""

    def __init__(
        self,
        username: str,
        password: str,
        pubkey: Path,
        socks_manager: SocksManager,
        hosts: list[str] | None = None,
        hosts_file: Path | None = None,
    ) -> None:
        """Constructor.

        :Parameters:
            - `username`: str, auth username.
            - `password`: str, auth password.
            - `hosts`: list, hosts list to transmit.
            - `hosts_file`: Path|None, path to file with hosts to transmit.
            - `pubkey`: Path, path to public key file.
            - `socks_manager`: SocksManager, Socks manager instance.
        """
        self._log = logging.getLogger(self.__class__.__name__)

        self._username = username
        self._password = password
        self._hosts: set[str] = set(hosts) if hosts else set()
        self._hosts_file = hosts_file
        self._pubkey_file = pubkey
        self._pubkey_data: str | None = None

        self._socks_manager = socks_manager

        self._ssh_client = SSHClient()
        self._ssh_client.set_missing_host_key_policy(AutoAddPolicy())

    def run(self) -> None:
        """Run SSH Key Transmitter."""
        self._run()

    def _run(self) -> None:
        if not self._pubkey_file:
            err_msg = 'Path to public key not provided. Cannot proceed.'
            self._log.error(err_msg)
            raise SSHKeyTransmitterError(err_msg)

        self._read_data()

        errored_hosts = self._transmit()
        if errored_hosts:
            self._log.warning('Errored hosts: %s', ', '.join(errored_hosts))

        self._log.info('Finished transmitting "%s"', self._pubkey_file)

    def _transmit(self) -> list[str]:
        errored_hosts: list[str] = []

        port: str | int
        for host_ in self._hosts:
            try:
                host, port = host_.split(':')
            except ValueError:
                self._log.warning(
                    'Using default SSH port %d for %s',
                    DEFAULT_SSH_PORT,
                    host_,
                )
                host = host_
                port = DEFAULT_SSH_PORT

            self._log.info('Transmitting public key to %s:%s', host, port)
            sock: socks.socksocket | None = None
            try:
                sock = self._socks_manager.create_socket(host, port)
                self._ssh_client.connect(
                    hostname=host,
                    port=int(port),
                    username=self._username,
                    password=self._password,
                    sock=sock,
                )
                self._put_public_key()
            except SSHKeyTransmitterError:
                errored_hosts.append(host)
            except AuthenticationException as err:
                self._log.error('Failed to authenticate to %s: %s', host, err)
                errored_hosts.append(host)
            except Exception:
                self._log.exception('Failed to transmit SSH files to "%s"', host)
                errored_hosts.append(host)
            finally:
                self._cleanup(sock=sock)
        return errored_hosts

    def _read_data(self) -> None:
        """Read public key and hosts file."""
        self._read_pubkey()
        if self._hosts_file:
            self._read_hosts_from_file()

    def _cleanup(self, sock: socks.socksocket | None = None) -> None:
        """Transmitter cleanup."""
        self._ssh_client.close()
        if sock:
            self._socks_manager.close_socket(sock=sock)

    def _put_public_key(self) -> None:
        """Transmit public key to connected host."""
        sftp = self._ssh_client.open_sftp()
        try:
            sftp.chdir(DEFAULT_SSH_DIR)
        except OSError:
            sftp.chdir('.')
            self._log.warning(
                'Directory "%s" does not exist. Will be created.',
                posixpath.join(sftp.getcwd(), DEFAULT_SSH_DIR),
            )
            self._create_ssh_dir(sftp)

        try:
            self._put_key(sftp)
        finally:
            sftp.close()

    @staticmethod
    def _create_ssh_dir(sftp: SFTPClient) -> None:
        """Create `DEFAULT_SSH_DIR` directory.

        :Parameters:
            - `sftp`: SFTPClient, paramiko sftp object.
        """
        sftp.mkdir(DEFAULT_SSH_DIR)
        sftp.chmod(DEFAULT_SSH_DIR, 0o700)
        sftp.chdir(DEFAULT_SSH_DIR)

    def _put_key(self, sftp: SFTPClient) -> None:
        """Transmit public key to connected host.

        :Parameters:
            - `sftp`: SFTPClient, paramiko sftp object.
        """
        remote_path = posixpath.join(sftp.getcwd(), DEFAULT_SSH_AUTH_KEYS)
        try:
            sftp.stat(DEFAULT_SSH_AUTH_KEYS)
        except OSError:
            # Create `DEFAULT_SSH_AUTH_KEYS` file
            self._log.warning('File "%s" does not exist. Will be created.', remote_path)
            self._create_ssh_auth_keys_file(sftp, remote_path)
            self._log.info(
                'Public key "%s" successfully added to %s',
                self._pubkey_file,
                remote_path,
            )
            return

        if not self._key_exists(sftp, remote_path):
            self._append_key(sftp, remote_path)

    def _create_ssh_auth_keys_file(self, sftp: SFTPClient, remote_path: str) -> None:
        """Create `DEFAULT_SSH_AUTH_KEYS` file.

        :Parameters:
            - `sftp`: SFTPClient, paramiko sftp object.
            - `remote_path`: str, remote path to key.
        """
        sftp.put(self._pubkey_file.as_posix(), remote_path)
        sftp.chmod(remote_path, 0o600)

    def _key_exists(self, sftp: SFTPClient, remote_path: str) -> bool:
        """Check if key exists.

        :Parameters:
            - `sftp`: SFTPClient, paramiko sftp object.
            - `remote_path`: str, remote path to key.
        """
        fd = sftp.file(DEFAULT_SSH_AUTH_KEYS, mode='r', bufsize=1)
        try:
            for line in fd:
                if line.strip() == self._pubkey_data:
                    self._log.warning(
                        'Public key "%s" already exists in "%s"',
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
            - `sftp`: SFTPClient, paramiko sftp object.
            - `remote_path`: str, remote path to key.
        """
        fd = sftp.file(DEFAULT_SSH_AUTH_KEYS, mode='a', bufsize=1)
        try:
            fd.write('\n' + self._pubkey_data)
            fd.flush()
        finally:
            fd.close()
        self._log.info(
            'Public key "%s" successfully appended to %s',
            self._pubkey_file,
            remote_path,
        )

    def _read_pubkey(self) -> None:
        """Read public key from file."""
        self._log.info('Reading public key from "%s"', self._pubkey_file)
        try:
            with self._pubkey_file.open() as fd_in:
                self._pubkey_data = fd_in.read().strip()
        except Exception as err:
            err_msg = f'Failed to read public key from "{self._pubkey_file}"'
            self._log.error(err_msg)
            raise DataReadError(err_msg) from err

    def _read_hosts_from_file(self) -> None:
        """Read hosts list from file."""
        self._log.info('Reading hosts list from "%s"', self._hosts_file)
        try:
            with self._hosts_file.open() as fd_in:
                self._hosts.update(fd_in.read().split())
        except Exception as err:
            err_msg = f'Failed to read hosts from "{self._hosts_file}"'
            self._log.error(err_msg)
            raise DataReadError(err_msg) from err
