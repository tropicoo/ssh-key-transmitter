from src.core.manager import SocksManager


def test_socks_manager_none() -> None:
    manager = SocksManager(socks_host=None, socks_port=None)
    assert manager.create_socket(dest_host='127.0.0.1', dest_port=80) is None
