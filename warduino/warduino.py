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

    def dump(self, save: bool = False, file_name: str = 'dump.json' ):
        globals, POSTFIX_INT
        msg = Interrupts['dump'] + POSTFIX_INT
        log.stderr_print(f"sending {msg.encode()}")
        self.socket.send(msg.encode())
        state = self.__receive_dump_helper()
        if save:
            data.save_state(file_name, state['str'])
        return state['parsed']

    def send_session(self, dmp, offset_emulator):
        encoded = cli.json2binary_and_b64(dmp, offset_emulator)
        for idx, m in enumerate(encoded['messages']):
            self.socket.send(m.encode())
            log.stderr_print(f'sending msg #{idx}')
            # if idx == len(encoded['messages']) - 1:
            #     log.stderr_print("waiting for done")
            #     self.socket.recv_until(b'done!\n')
            # else:
            #     log.stderr_print("waiting for ack")
            #     self.socket.recv_until(b'ack!\n')
        log.stderr_print("waiting for done!")
        self.socket.recv_until(b'done!\n')

    def run(self):
        globals, POSTFIX_INT
        msg = Interrupts['run'] + POSTFIX_INT
        log.stderr_print(f"sending {msg.encode()}")
        self.socket.send(msg.encode())
        self.socket.recv_until(b"GO!\n")
        

    def register_rfc(self, host: str, port: int, func_ids: List[int]) -> str:
        payload = cli.encode_monitor_proxies(host, port, func_ids)
        self.socket.send(payload.encode())

    def disconnect(self):
        self.socket.disconnect()

    def __receive_dump_helper(self):
        sock = self.socket
        _noise = sock.recv_until(b'DUMP!\n')
        json_bytes = sock.recv_until(b'\n')[:-len(b'\n')]
        try:
            dec = json_bytes.decode()
            parsed = json.loads(dec)
            len_cs = len(parsed['callstack'])
            len_vals = len(parsed['stack'])
            log.stderr_print(f'callstack #{len_cs} stack #{len_vals}')
            return {"str": dec, "parsed": parsed}
        except: 
            log.stderr_print(f"failed for raw {json_bytes}")
            raise ValueError("something wrong")

    # TEST METHODS 

    def test_send_fac_session(self):
        dmp = self.dump()
        self.send_session(data.fac_state(), dmp['start'][0])

    def test_send_blink_session(self):
        dmp = self.dump()
        self.snapshot = dmp
        self.send_session(data.state_blink_led(), dmp['start'][0])

    def test_bin_encode(self):
        globals, POSTFIX_INT
        msg = Interrupts['dump'] + POSTFIX_INT
        log.stderr_print(f"sending {msg.encode()}")
        self.socket.send(msg.encode())
        state = self.__receive_dump_helper()['str']
        encoded = cli.json2binary_and_b64(state, data.fac_state()['start'][0])


wd = WARDuino()
wd.connect()
#wd.register_rfc("192.168.0.130", 8080, [2, 3, 1])
