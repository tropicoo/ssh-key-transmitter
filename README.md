SSH Key Transmitter
====================

Bored to log in to remote servers through SSH every time using username/password
combination?

This simple app will help you to transmit your SSH Public Key to your hosts.

Need to connect through SOCKS5 proxy? No worries, it will do the job.

> Sidenote: No really practical use case for this app, but it was fun to write it.

```bash
$ python3 ssh-key-transmit.py -hosts 10.10.10.10 -u tropicoo -p my_passwd -pk id_rsa_2048_ubuntu.pub --socks-host 127.0.0.1 --socks-port 1080




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
Python 3.12+, Paramiko, PySocks, Typer.

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

```bash
$ python3 ssh-key-transmit.py --help

 Usage: ssh-key-transmit.py [OPTIONS]                                                       

 SSH Key Transmitter.

╭─ Options ────────────────────────────────────────────────────────────────────────────────╮
│ *  --username    -u          TEXT                     auth username [required]           │
│ *  --password    -p          TEXT                     auth password [required]           │
│ *  --pub-key     -pk         FILE                     path to public key file [required] │
│    --socks-host              TEXT                     socks5 proxy host                  │
│    --socks-port              INTEGER                  socks5 proxy port                  │
│    --hosts-file              FILE                     path to file with hosts list       │
│                  -hosts      TEXT                     host(s) to transmit ssh public key │
│    --verbose     -v          INTEGER RANGE [0<=x<=3]  log level 0-3. Default 2 (INFO)    │
│                                                       [default: 2]                       │
│    --version     -V                                   show application version           │
│    --help                                             Show this message and exit.        │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```

#### Some details

| Argument     | Description                                                                         |
|:-------------|:------------------------------------------------------------------------------------|
| -hosts       | One or more hosts separated by space, accepted format \<HOST\> or \<HOST\>:\<PORT\> |
| --hosts-file | Path to text file with list of hosts separated by comma or spaces                   |
