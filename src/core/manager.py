import socks


class SocksManager:
    """Socks manager class."""

    def __init__(self, socks_host: str | None, socks_port: int | None) -> None:
        """Constructor.

        :Parameters:
            - `socks_host`: str, SOCKS5 proxy host.
            - `socks_port`: str, SOCKS5 proxy port.
        """
        self._host = socks_host
        self._port = socks_port

    def create_socket(
        self,
        dest_host: str,
        dest_port: str | int,
    ) -> socks.socksocket | None:
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

    @staticmethod
    def close_socket(sock: socks.socksocket) -> None:
        sock.close()
