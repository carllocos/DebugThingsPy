import socket


def valid_addr(addr: str) -> bool:
    if addr == "localhost":
        return True
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False

