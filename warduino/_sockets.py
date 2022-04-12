from __future__ import annotations
from typing import Union, List, Any

import socket
import select
import time
import mylogger as log

# import os
# import inspect
# import signal
# import sys

class SocketWrapper:

    def __init__(self, sock):
        self.__sock = sock
        self.__recvbuff = b''
        self.__connected = True

    @property
    def recvbuff(self):
        return self.__recvbuff

    @recvbuff.setter
    def recvbuff(self, b):
        self.__recvbuff = b

    @property
    def socket(self):
        return self.__sock

    @property
    def connected(self) -> bool:
        return self.__connected
    
    def close(self) -> None:
        log.stderr_print("closing socket")
        self.__sock.close()
        self.__connected = False

    def send(self, d):
        return self.socket.send(d)

    def recv(self, d, timeout = False):
        if timeout:
            deadline = time.time() + 3
            self.socket.settimeout(deadline)

        return self.socket.recv(d)

    def add_bytes(self, b):
        self.__recvbuff += b

    def pop_until(self, until: bytes) -> Union[bytes, None]:
        pos = self.recvbuff.find(until)
        if pos < 0:
            return None

        end = pos + len(until)
        remain = self.recvbuff[end:]
        buff = self.recvbuff[:end]
        self.recvbuff = remain
        return buff

class Sockets:
    def __init__(self, host, port, _maxsend= 1024):
        self.__port = port
        self.__host = host
        self.__socket = None
        self.__maxsendbytes = _maxsend
        self.__recvbuff_size = _maxsend     #TODO change


    @property
    def connected(self) -> bool:
        if self.socket is None:
            return False
        elif not self.socket.connected:
            return False
        elif self.event_socket is None:
            return False
        elif not self.event_socket.connected:
            return False

        return True

    @property
    def port(self) -> int:
        return self.__port

    @property
    def host(self) -> str:
        return self.__host

    @property
    def recvbuff_size(self) -> int:
        return self.__recvbuff_size

    def connect(self) -> bool:
        log.stderr_print(f'connecting to {self.host} {self.port}')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        self.__socket = SocketWrapper(sock)

        return True

    def send(self, content):
        self.__socket.send(content)

    def recv_until(self, until: bytes, wait: bool = True) -> bytes:

        aSocket = self.__socket
        if len(aSocket.recvbuff) > 0:
            _bytes = aSocket.pop_until(until)
            if _bytes is not None:
                return _bytes

        while wait:
            if not aSocket.connected:
                return b''

            _bytes = aSocket.recv(self.recvbuff_size)
            if len(_bytes) == 0:
                log.stderr_print("connection closed")
                aSocket.close()
                return b''

            aSocket.add_bytes(_bytes)
            _bytes = aSocket.pop_until(until)
            if _bytes is not None:
                return _bytes
