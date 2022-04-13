from __future__ import annotations
from typing import Union, List, Any

from _sockets import Sockets
import select
import json

import cli
import data
import mylogger as log

Interrupts = {
    'run': '01',
    'bpadd': '06',
    'bprmv': '07',
    'dump': '60',
    'offset': '61',
    'recv_state': '62'}


POSTFIX_INT = ' \n'
class WARDuino:
    def __init__(self):
        self.socket = Sockets('localhost', 8192)
        self.snapshot = None

    def connect(self):
        self.socket.connect()

    def dump(self):
        globals, POSTFIX_INT
        msg = Interrupts['dump'] + POSTFIX_INT
        log.stderr_print(f"sending {msg.encode()}")
        self.socket.send(msg.encode())
        return self.__receive_dump_helper()

    def test_send_fac_session(self):
        dmp = self.dump()
        self.snapshot = dmp
        self.send_session(data.fac_state(), dmp['start'][0])

    def test_send_blink_session(self):
        dmp = self.dump()
        self.snapshot = dmp
        self.send_session(data.state_blink_led(), dmp['start'][0])

    def send_session(self, dmp, offset_emulator):
        encoded = cli.json2binary(dmp, offset_emulator)
        for idx, m in enumerate(encoded['messages']):
            self.socket.send(m.encode())
            log.stderr_print(f'sending msg #{idx}')
            if idx == len(encoded['messages']) - 1:
                log.stderr_print("waiting for done")
                self.socket.recv_until(b'done!\n')
            else:
                log.stderr_print("waiting for ack")
                self.socket.recv_until(b'ack!\n')

    def run(self):
        globals, POSTFIX_INT
        msg = Interrupts['run'] + POSTFIX_INT
        log.stderr_print(f"sending {msg.encode()}")
        self.socket.send(msg.encode())
        self.socket.recv_until(b"GO!\n")
        
    def __receive_dump_helper(self):

        sock = self.socket
        _noise = sock.recv_until(b'DUMP!\n')

        raw_end = b']}'
        re_len = len(raw_end)

        json_bytes = b''
        json_bytes += sock.recv_until(b'"elements":[') + raw_end
        elements = sock.recv_until(raw_end)[:-re_len]
        json_bytes += sock.recv_until(b'"bytes":[') + raw_end
        membytes = sock.recv_until(raw_end)[:-2]
        json_bytes += sock.recv_until(b'"labels":[') + raw_end
        labels = sock.recv_until(raw_end)[:-re_len]
        json_bytes += sock.recv_until(b'\n')[:-len(b'\n')]

        dec=None
        try:
            dec = json_bytes.decode()
        except: 
            log.stderr_print(f"failed for raw {json_bytes}")
            raise ValueError("something wrong")

        parsed = json.loads(dec)
        parsed['memory']['bytes'] = membytes
        parsed['table']['elements'] = elements
        br_tbl = parsed['br_table']
        br_tbl['size'] = br_tbl['size']
        br_tbl['labels'] = labels

        len_cs = len(parsed['callstack'])
        len_vals = len(parsed['stack'])
        log.stderr_print(f'callstack #{len_cs} stack #{len_vals}')
        return parsed


wd = WARDuino()
wd.connect()
