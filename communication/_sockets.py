from __future__ import annotations
from typing import Union, List, Any

import os
import socket
import inspect
import signal
import sys
import select

from utils import dbgprint, errprint
from interfaces import AMedium, AMessage

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
        print("closing socket")
        self.__sock.close()
        self.__connected = False

    def send(self, d):
        return self.socket.send(d)

    def recv(self, d):
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

class Sockets(AMedium):
    def __init__(self, port, host, _maxsend= 1024):
        self.__port = port
        self.__host = clean_host(host)
        self.__serializer = None
        self.__socket = None
        self.__evsocket = None
        self.__fp = None

        assert _maxsend > 0, f'{_maxsend} > {0}'
        self.__maxsendbytes = _maxsend
        self.__recvbuff_size = _maxsend     #TODO change


    #TODO remove
    @property
    def is_socket(self)-> bool:
        return True

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
    def serializer(self):
        return self.__serializer

    @serializer.setter
    def serializer(self, s):
        self.__serializer = s

    @property
    def socket(self) -> SocketWrapper:
        return self.__socket

    @property
    def event_socket(self) -> SocketWrapper:
        return self.__evsocket

    def getsockets(self):
        return (self.socket, self.event_socket)

    @property
    def recvbuff_size(self) -> int:
        return self.__recvbuff_size

    #API
    def start_connection(self, dev) -> bool:
        #FIXME add try catch
        dbgprint(f'connecting at {self.host} port {self.port}')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        evsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        evsock.connect((self.host, self.port))

        self.__socket = SocketWrapper(sock)
        self.__evsocket = SocketWrapper(evsock)

        return True

    def close_connection(self, dev):
        raise NotImplementedError

    def discover_devices(self):
        raise NotImplementedError


    def send(self, msgs: Union[AMessage, List[AMessage]]) -> List[Any]:
        messages = msgs
        if not isinstance(msgs, list):
            messages= [msgs]

        replies = []
        for m in messages:
            dbgprint(f'message {m.content}')
            self.__socket.send(m.content.encode())
            if m.has_reply():
                r = m.get_reply(self.serializer, self)
                replies.append(r)
        if isinstance(msgs, list):
            return replies
        else:
            return replies[0]

    def has_event(self, timeout: float) -> bool:
        if len(self.event_socket.recvbuff) > 0:
            return True

        if not self.event_socket.connected:
            return False

        evsock = self.event_socket.socket
        io_sock = self.socket.socket
        ready, _, err = select.select([evsock], [],[evsock, io_sock], timeout)

        for e in err:
            if e == io_sock:
                self.socket.close()
            else:
                self.event_socket.close()
        return len(ready) > 0

    def recv_until(self, until: Union[List[bytes], bytes], event:bool = False, wait: bool = True) -> bytes:
        aSocket =  self.event_socket if event else self.socket
        _untils = until
        if isinstance(until, bytes):
            _untils = [until]

        if len(aSocket.recvbuff) > 0:
            for u in _untils:
                _bytes = aSocket.pop_until(u)
                if _bytes is not None:
                    return _bytes

        while wait:
            if not aSocket.connected:
                return b''

            _bytes = aSocket.recv(self.recvbuff_size)
            if len(_bytes) == 0:
                print("closing connection")
                dbgprint("connection closed")
                aSocket.close()
                return b''

            aSocket.add_bytes(_bytes)
            for u in _untils:
                _bytes = aSocket.pop_until(u)
                if _bytes is not None:
                    return _bytes

def clean_host(h: str) -> str:
    cleaned = h.lower().strip()
    if cleaned == 'localhost' or cleaned == '127.0.0.1':
        return 'localhost'
    else:
        return cleaned