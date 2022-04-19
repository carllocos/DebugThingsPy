from __future__ import annotations
from typing import Union, List, Any

import socket
import select
import sys


if __name__ == "__main__":
    port = int(sys.argv[1])
    host = '127.0.0.1'
    print(f"start server at {host} {port}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen()
    conn, addr = sock.accept()
    print(f"connect by addr {addr}")

    while True:
        data = conn.recv(1024)
        if data == b'':
            break
        print(data)
