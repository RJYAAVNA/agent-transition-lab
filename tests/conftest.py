import socket

import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_dns(*args: object, **kwargs: object) -> None:
        pytest.fail("Use a test double for external network requests.")

    def loopback_only(connect):
        def checked_connect(sock, address):
            # Windows asyncio builds its internal socket pair over loopback.
            if sock.family in (socket.AF_INET, socket.AF_INET6):
                if address[0] not in ("127.0.0.1", "::1"):
                    pytest.fail("Use a test double for external network requests.")
            return connect(sock, address)

        return checked_connect

    monkeypatch.setattr(socket, "getaddrinfo", reject_dns)
    monkeypatch.setattr(socket.socket, "connect", loopback_only(socket.socket.connect))
    monkeypatch.setattr(socket.socket, "connect_ex", loopback_only(socket.socket.connect_ex))
