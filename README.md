SSH Key Transmitter
====================

Bored to log in to remote servers through SSH every time using username/password
combination?

This simple script will help to transmit your SSH Public Key to them.

Need to connect through SOCKS5 proxy? No worries, it will do the job.

```bash
$ python3 ssh-key-transmit.py -hosts 10.10.10.10 -u tropicoo -p my_passwd -pkey id_rsa_2048_ubuntu.pub --socks-host 127.0.0.1 --socks-port 1080




███████╗███████╗██╗  ██╗    ██╗  ██╗███████╗██╗   ██╗    ████████╗██████╗  █████╗ ███╗   ██╗███████╗███╗   ███╗██╗████████╗████████╗███████╗██████╗
██╔════╝██╔════╝██║  ██║    ██║ ██╔╝██╔════╝╚██╗ ██╔╝    ╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝████╗ ████║██║╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗
███████╗███████╗███████║    █████╔╝ █████╗   ╚████╔╝        ██║   ██████╔╝███████║██╔██╗ ██║███████╗██╔████╔██║██║   ██║      ██║   █████╗  ██████╔╝
╚════██║╚════██║██╔══██║    ██╔═██╗ ██╔══╝    ╚██╔╝         ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██║╚██╔╝██║██║   ██║      ██║   ██╔══╝  ██╔══██╗
███████║███████║██║  ██║    ██║  ██╗███████╗   ██║          ██║   ██║  ██║██║  ██║██║ ╚████║███████║██║ ╚═╝ ██║██║   ██║      ██║   ███████╗██║  ██║
╚══════╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝   ╚═╝          ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚═╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝



2019-05-14 23:49:55,310 - SSHKeyTransmitter - INFO - [__init__] - Using SOCKS5 proxy 127.0.0.1:1080
2019-05-14 23:49:55,313 - SSHKeyTransmitter - INFO - [run] - Transmitting public key to 10.10.10.15:22
2019-05-14 23:49:56,471 - SSHKeyTransmitter - INFO - [_put_key] - Public key id_rsa_2048_ubuntu.pub successfully appended to /home/tropicoo/.ssh/authorized_keys
```

Requirements
------------
Python 3.10+, Paramiko, PySocks.

Installation
------------

```
git clone https://github.com/tropicoo/ssh-key-transmitter.git
cd ssh-key-transmitter
pip3 install -r requirements.txt
```

Usage
-----
> Hosts or path to file with hosts, username, password and path to public key
> file are mandatory.

```
$ python3 ssh-key-transmit.py -h
usage: ssh-key-transmit.py [-h] [-hosts HOSTS [HOSTS ...]] [-u USERNAME]
                           [-p PASSWORD] [-pkey PUBKEY]
                           [--hosts-file HOSTS_FILE] [--socks-host SOCKS_HOST]
                           [--socks-port SOCKS_PORT]

SSH Key Transmitter

optional arguments:
  -h, --help            show this help message and exit
  -hosts HOSTS [HOSTS ...]
                        host(s) to transmit ssh public key
  -u USERNAME, --username USERNAME
                        auth username
  -p PASSWORD, --password PASSWORD
                        auth password
  -pkey PUBKEY, --pub-key PUBKEY
                        path to public key
  --hosts-file HOSTS_FILE
                        path to file with hosts list
  --socks-host SOCKS_HOST
                        socks5 proxy host
  --socks-port SOCKS_PORT
                        socks5 proxy port
```

#### Some details

| Argument     | Description                                                                         |
|:-------------|:------------------------------------------------------------------------------------|
| -hosts       | One or more hosts separated by comma, accepted format \<HOST\> or \<HOST\>:\<PORT\> |
| --hosts-file | Path to text file with list of hosts separated by comma or spaces                   |
