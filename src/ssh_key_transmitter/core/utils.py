from paramiko import AutoAddPolicy, SSHClient


def create_ssh_client(*, set_missing_host_key_policy: bool = True) -> SSHClient:
    ssh_client = SSHClient()
    if set_missing_host_key_policy:
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())  # noqa: S507 # nosec: B507
    return ssh_client
