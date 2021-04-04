import os
import socket
import inspect
import signal
import sys
import select
import threading

from communication import medium
from communication import request as req

DEBUG = True

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

    @property
    def socket(self):
        return self.__sock

    def change_buf(self, b):
        self.__recvbuff = b

    def send(self, d):
        return self.socket.send(d)

    def recv(self, d):
        return self.socket.recv(d)

    def add_bytes(self, b):
        self.__recvbuff += b

class Socket(medium.Medium):

    def __init__(self, serializer):
        self.__serializer = serializer
        self.__socket = None
        self.__sockAtBp = None
        self.__PORT = 8080
        self.__HOST = 'localhost'
        self.__fp = None
        self.__maxsendbytes = None
    #API
    def start_connection(self, dev):
        HOST = self.__HOST
        PORT = self.__PORT

        flags_io = 3
        flags_ev = 16
        # flags_dbg =8
        b_flags_io = int(flags_io).to_bytes(1, 'big')
        b_flags_ev = int(flags_ev).to_bytes(1, 'big')
        # b_flags_dbg = int(flags_dbg).to_bytes(1, 'big')

        dbgprint(f'connecting to socket at {self.__HOST} port {self.__PORT}')
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sockAtBp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.__sockDBG = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.__socket.connect((HOST, PORT))
        # self.__sockDBG.connect((HOST, PORT))
        self.__sockAtBp.connect((HOST, PORT))

        # self.__sockDBG.send((b_flags_dbg))
        # buf_dbg = self.__sockDBG.recv(10)
        # assert flags_dbg == buf_dbg[0], f'{flags_dbg} == {buf_dbg[0]}'

        self.__socket.send(b_flags_io)
        buf_io = self.__socket.recv(10)
        print(f'bytes buf_io {buf_io}')
        assert flags_io == buf_io[0], f'{flags_io} == {buf_io[0]}'

        self.__sockAtBp.send(b_flags_ev)
        buf_ev = self.__sockAtBp.recv(10)
        assert flags_ev == buf_ev[0], f'buffer event {buf_ev}'

        # dbgthr = threading.Thread(target=start_recvdbg, args=(self.__sockDBG,))
        # dbgthr.start()
        wait_for_quantity = len(buf_io) < 5
        while wait_for_quantity:
            ready = select.select([self.__socket], [],[], 1)
            if not ready[0]:
                continue
            buf_io += self.__socket.recv(10)
            wait_for_quantity = len(buf_io) < 5

        self.__sockAtBp = SocketWrapper(self.__sockAtBp)
        self.__socket = SocketWrapper(self.__socket)
        maxsendbytes = int.from_bytes(buf_io[1:5], byteorder='little', signed=False)
        assert maxsendbytes > 0, f'{maxsendbytes} > {0}'
        self.__serializer.max_bytes = maxsendbytes

        return True

    def close_connection(self, dev):
        raise NotImplementedError

    def discover_devices(self):
        raise NotImplementedError

    # def send_str(self, content, dev):
    #     self.__fp.seek(0)
    #     self.__fp.truncate()
    #     self.__fp.write(content)
    #     self.__fp.flush()
    #     p = dev.process
    #     os.kill(p.info.get('pid'), signal.SIGUSR1)

    def send(self, messages, dev):
        for m in messages:
            # self.send_str(m.content, dev)
            self.__socket.send(m.content.encode())
            if m.has_reply():
                m.get_reply(self.__serializer, self)
        return messages

    #helper methods
    def wait_for_answers(self, messages):
        return 'done'

    def open_tmp_file(self, name='change'):
        path = '/tmp/'
        self.__fp = open(os.path.join(path, name),'w')
        dbgprint(f'File {name} open at {path}')

    def getsockets(self):
        return (self.__socket, self.__sockAtBp)

    def recv_bytes(self, until=None, aSocket=None):

        if aSocket is None:
            aSocket = self.__socket 

        buffsize  = 1024

        if until is None:
            errprint('until is None')

        if len(aSocket.recvbuff) > 0:
            pos = aSocket.recvbuff.find(until)
            dbgprint('from accumulated!')
            if pos != -1:
                end = pos + len(until)
                remain = aSocket.recvbuff[end:]
                buff = aSocket.recvbuff[:end]
                aSocket.change_buf(remain)
                return buff

        while True:
            aSocket.add_bytes(aSocket.recv(buffsize))
            pos = aSocket.recvbuff.find(until)
            if pos != -1:
                dbgprint(f'from accr {aSocket.recvbuff}')
                end = pos + len(until)
                remain = aSocket.recvbuff[end:]
                buff = aSocket.recvbuff[:end]
                aSocket.change_buf(remain)
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

