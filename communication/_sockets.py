from __future__ import annotations
from typing import Union, List, Any

import os
import socket
import inspect
import signal
import sys
import select


from interfaces import AMedium, AMessage

DEBUG = False

def dbgprint(s):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    cn =str(calframe[1][3])
    if DEBUG:# and cn in ONLY:
        print((cn + ':').upper(), s)

def errprint(s):
    print(s)
    sys.exit()

class SocketWrapper:

    def __init__(self, sock):
        self.__sock = sock
        self.__recvbuff = b''

    @property
    def recvbuff(self):
        return self.__recvbuff

    @recvbuff.setter
    def recvbuff(self, b):
        self.__recvbuff = b

    @property
    def socket(self):
        return self.__sock


    def send(self, d):
        return self.socket.send(d)

    def recv(self, d):
        return self.socket.recv(d)

    def add_bytes(self, b):
        self.__recvbuff += b

class Sockets(AMedium):
    def __init__(self, port, host, _maxsend= 1024):
        self.__port = port
        self.__host = clean_host(host)
        self.__serializer = None
        self.__socket = None
        self.__sockAtBp = None
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
        return self.__socket is not None

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
        return self.__sockAtBp

    def getsockets(self):
        return (self.socket, self.event_socket)

    @property
    def recvbuff_size(self) -> int:
        return self.__recvbuff_size

    #API
    def start_connection(self, dev) -> bool:
        dbgprint(f'connecting at {self.host} port {self.port}')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        evsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        evsock.connect((self.host, self.port))

        self.__socket = SocketWrapper(sock)
        self.__sockAtBp = SocketWrapper(evsock)

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
        sock = self.event_socket.socket
        ready, _, err = select.select([sock], [],[sock], timeout)
        if err:
            errprint(f'socket has error {err}')
        return len(ready) > 0

    def recv_bytes(self, until: Union[bytes, None] = None, event:bool = False) -> bytes:
        aSocket =  self.event_socket if event else self.socket

        if until is None:
            errprint('until is None')

        if len(aSocket.recvbuff) > 0:
            pos = aSocket.recvbuff.find(until)
            dbgprint('from accumulated!')
            if pos != -1:
                end = pos + len(until)
                remain = aSocket.recvbuff[end:]
                buff = aSocket.recvbuff[:end]
                aSocket.recvbuff = remain
                return buff

        while True:
            aSocket.add_bytes(aSocket.recv(self.recvbuff_size))
            pos = aSocket.recvbuff.find(until)
            if pos != -1:
                dbgprint(f'from accr {aSocket.recvbuff}')
                end = pos + len(until)
                remain = aSocket.recvbuff[end:]
                buff = aSocket.recvbuff[:end]
                aSocket.recvbuff = remain
                return buff

def start_recvdbg(sock):
    print("START receive Debug info")
    timeout_secs = 1
    _buff = b''
    while True:
        ready = select.select([sock], [],[], timeout_secs)
        if not ready[0]:
            continue

        _buff += sock.recv(1024)
        try:
            print(_buff.decode(), end="")
            _buff = b''
        except:
            print( "failed to decode")

def clean_host(h: str) -> str:
    cleaned = h.lower().strip()
    if cleaned == 'localhost' or cleaned == '127.0.0.1':
        return 'localhost'
    else:
        return cleaned