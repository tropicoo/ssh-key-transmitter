#!/usr/bin/env python3
"""SSH Key Transmitter Module."""

import argparse
import logging
import posixpath
import sys

import paramiko
import socks


BANNER = """


███████╗███████╗██╗  ██╗    ██╗  ██╗███████╗██╗   ██╗    ████████╗██████╗  █████╗ ███╗   ██╗███████╗███╗   ███╗██╗████████╗████████╗███████╗██████╗ 
██╔════╝██╔════╝██║  ██║    ██║ ██╔╝██╔════╝╚██╗ ██╔╝    ╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝████╗ ████║██║╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗
███████╗███████╗███████║    █████╔╝ █████╗   ╚████╔╝        ██║   ██████╔╝███████║██╔██╗ ██║███████╗██╔████╔██║██║   ██║      ██║   █████╗  ██████╔╝
╚════██║╚════██║██╔══██║    ██╔═██╗ ██╔══╝    ╚██╔╝         ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██║╚██╔╝██║██║   ██║      ██║   ██╔══╝  ██╔══██╗
███████║███████║██║  ██║    ██║  ██╗███████╗   ██║          ██║   ██║  ██║██║  ██║██║ ╚████║███████║██║ ╚═╝ ██║██║   ██║      ██║   ███████╗██║  ██║
╚══════╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝   ╚═╝          ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚═╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝


"""
SSH_PORT = 22
SSH_DIR = '.ssh'
SSH_AUTH_KEYS = 'authorized_keys'

EXIT_OK = 0
EXIT_ERROR = 1


class SSHKeyTransmitterError(Exception):
    """SSH Key Transmitter Base Error Class."""
    pass


class SSHKeyTransmitter:
    """SSH Key Transmitter Class."""

    def __init__(self, username, password, pubkey, hosts=None,
                 hosts_file=None, socks_host=None, socks_port=None):
        """Constructor.

        :Parameters:
            - `username`: str, auth username.
            - `password`: str, auth password.
            - `hosts`: list, hosts list to transmit.
            - `hosts_file`: str, path to file with hosts to transmit.
            - `pubkey`: str, path to public key file.
            - `socks_host`: str, SOCKS5 proxy host.
            - `socks_port`: str, SOCKS5 proxy port.
        """
        self._log = logging.getLogger('SSHKeyTransmitter')
        logging.getLogger('paramiko').setLevel(logging.WARNING)

        self._username = username
        self._password = password
        self._hosts = set(hosts) if hosts else set()
        self._hosts_file = hosts_file
        self._pubkey_file = pubkey
        self._pubkey_data = None

        self._socks_host = socks_host
        self._socks_port = socks_port
        self._socks = None

        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def run(self):
        """Run SSH Key Transmitter.

        :Return
            - Boolean value indicating if transmit failed on any host.
        """
        exit_code = EXIT_OK
        errored_hosts = []

        if not self._pubkey_file:
            self._log.error('Path to public key not provided. '
                            'Can\'t proceed.')
            return EXIT_ERROR

        try:
            self._read_pubkey()
            if self._hosts_file:
                self._read_hosts_from_file()
        except SSHKeyTransmitterError:
            return EXIT_ERROR

        for host in self._hosts:
            try:
                host, port = host.split(':')
            except ValueError:
                port = SSH_PORT

            try:
                self._log.info('Transmitting public key to %s:%s', host, port)

                self._create_socks()
                if self._socks:
                    self._socks.connect((host, port))
                self._ssh.connect(hostname=host, port=port,
                                  username=self._username,
                                  password=self._password,
                                  sock=self._socks)
                self._put_public_key()
            except SSHKeyTransmitterError:
                exit_code = EXIT_ERROR
                errored_hosts.append(host)
            except paramiko.ssh_exception.AuthenticationException as err:
                self._log.error('Failed to authenticate to %s: %s',
                                host, str(err))
                exit_code = EXIT_ERROR
                errored_hosts.append(host)
            except Exception:
                self._log.exception('Failed to transmit SSH files to %s', host)
                exit_code = EXIT_ERROR
                errored_hosts.append(host)
            finally:
                if self._ssh.get_transport():
                    self._ssh.close()
                if self._socks:
                    self._socks.close()
                    self._socks = None
        if errored_hosts:
            self._log.warning('Errored hosts: %s', ', '.join(errored_hosts))
        self._log.info('Finished transmitting %s', self._pubkey_file)
        return exit_code

    def _create_socks(self):
        if self._socks_host and self._socks_port:
            self._socks = socks.socksocket()
            self._socks.set_proxy(proxy_type=socks.SOCKS5,
                                  addr=self._socks_host,
                                  port=int(self._socks_port))

    def _put_public_key(self):
        """Transmit public key to connected host."""
        sftp = self._ssh.open_sftp()
        try:
            # Throw IOError if directory doesn't exist
            sftp.chdir(SSH_DIR)
            self._put_key(sftp)
        except IOError:
            # Create SSH_DIR
            sftp.chdir('.')
            self._log.warning('Directory %s doesn\'t exist. Will be created.',
                              posixpath.join(sftp.getcwd(), SSH_DIR))
            sftp.mkdir(SSH_DIR)
            sftp.chmod(SSH_DIR, 0o700)
            sftp.chdir(SSH_DIR)
            self._put_key(sftp)
        finally:
            sftp.close()

    def _put_key(self, sftp):
        """Transmit public key to connected host.

        :Parameters:
            - `sftp`: obj, paramiko sftp object.
        """
        remote_path = posixpath.join(sftp.getcwd(), SSH_AUTH_KEYS)
        try:
            # Throw IOError if file doesn't exist
            sftp.stat(SSH_AUTH_KEYS)

            # Check if key exists
            fd = sftp.file(SSH_AUTH_KEYS, mode='r', bufsize=1)
            try:
                for line in fd:
                    if line.strip() == self._pubkey_data:
                        self._log.warning('Public key %s already exists in %s',
                                          self._pubkey_file, remote_path)
                        return
            finally:
                fd.close()

            # Append key
            fd = sftp.file(SSH_AUTH_KEYS, mode='a', bufsize=1)
            try:
                fd.write('\n' + self._pubkey_data)
                fd.flush()
            finally:
                fd.close()

            self._log.info('Public key %s successfully appended to %s',
                           self._pubkey_file, remote_path)
        except IOError:
            # Create SSH_AUTH_KEYS file
            self._log.warning('File %s doesn\'t exist. Will be created.',
                              remote_path)

            sftp.put(self._pubkey_file, remote_path)
            sftp.chmod(remote_path, 0o600)

            self._log.info('Public key %s successfully added to %s',
                           self._pubkey_file, remote_path)

    def _read_pubkey(self):
        """Read public key from file."""
        self._log.info('Reading public key from %s', self._pubkey_file)
        try:
            with open(self._pubkey_file, 'r') as fd:
                self._pubkey_data = fd.read().strip()
        except Exception:
            err_msg = 'Failed to read public key from {0}'.format(
                self._pubkey_file)
            self._log.exception(err_msg)
            raise SSHKeyTransmitterError(err_msg)

    def _read_hosts_from_file(self):
        """Read hosts list from file."""
        self._log.info('Reading hosts list from %s', self._hosts_file)
        try:
            with open(self._hosts_file, 'r') as fd:
                self._hosts.update(fd.read().split())
        except Exception:
            err_msg = 'Failed to read hosts from {0}'.format(self._hosts_file)
            self._log.exception(err_msg)
            raise SSHKeyTransmitterError(err_msg)


def main():
    """Main function."""
    print(BANNER)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO,
                        stream=sys.stdout)

    parser = argparse.ArgumentParser(description='SSH Key Transmitter')
    parser.add_argument('-hosts', default=None, nargs='+',
                        help='host(s) to transmit ssh public key')
    parser.add_argument('-u', '--username', action='store',
                        default=None,
                        dest='username',
                        help='auth username')
    parser.add_argument('-p', '--password', action='store',
                        default=None,
                        dest='password',
                        help='auth password')
    parser.add_argument('-pkey', '--pub-key', action='store',
                        default=None,
                        dest='pubkey',
                        help='path to public key')
    parser.add_argument('--hosts-file', action='store',
                        default=None,
                        dest='hosts_file',
                        help='path to file with hosts list')
    parser.add_argument('--socks-host', action='store',
                        default=None,
                        dest='socks_host',
                        help='socks5 proxy host')
    parser.add_argument('--socks-port', action='store',
                        default=None,
                        dest='socks_port',
                        help='socks5 proxy port')

    args = parser.parse_args()
    if not all([args.pubkey, args.username, args.password]) or \
            not any([args.hosts, args.hosts_file]):
        parser.print_help()
        return EXIT_ERROR

    transmitter = SSHKeyTransmitter(username=args.username,
                                    password=args.password,
                                    pubkey=args.pubkey,
                                    hosts=args.hosts,
                                    hosts_file=args.hosts_file,
                                    socks_host=args.socks_host,
                                    socks_port=args.socks_port)

    return transmitter.run()


if __name__ == '__main__':
    sys.exit(main())
