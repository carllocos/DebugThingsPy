from __future__ import annotations
from typing import Union

import sys
import inspect
import json
from threading import Thread
import math
import select
import struct

from interfaces import ASerial, AMessage, AMedium
from utils import util, dbgprint, errprint, infoprint
from . import encoder

AnsProtocol = {
    'dump': '10',
    'locals': '11',
    'receivesession': '22',
    'rmvbp': '07',
    'run': 'GO!\n',
    'step': 'STEP!\n',
    'pause': 'PAUSE!\n'
}


Interrupts = {
    'addbp': '06',
    'dump': '60',
    'offset': '0x61',
    'locals': '11',
    'receivesession': '62',
    'recvproxies': '25',
    'rmvbp': '07',
    'run': '01',
    'step': '04',
    'until': '05',
    'updateModule' : '24',
    'pause': '03'
}

proxy_config = None

class WOODManager(ASerial):
    def __init__(self):
        super().__init__()
        self.__offset = None
        self.__max_bytes = 1024  # FIXME at 20 get issue due to pc_serialization
        self.__medium = None
        self.__redirectdbg = None
        self.__connected = False
        self.__eventlistener = None
        self.__event_handler = None

    #properties
    @property
    def medium(self) -> AMedium:
        return self.__medium

    @medium.setter
    def medium(self, m):
        self.__medium = m
        self.__medium.serializer = self

    @property
    def max_bytes(self):
        return self.__max_bytes

    @max_bytes.setter
    def max_bytes(self, v):
        self.__max_bytes = v

    @property
    def connected(self) -> bool:
        return self.__connected

    @connected.setter
    def connected(self, c: bool) -> None:
        self.__connected = c


    @property
    def uses_socket(self) -> bool:
        return self.medium.is_socket

    @property
    def debugger(self):
        return self.__debugger

    def set_debugger(self, d):
        self.__debugger = d

    def redirect_dbg(self, dbg_med):
        self.__redirectdbg = dbg_med

    def set_event_handler(self, eh: callable) -> None:
        self.__event_handler = eh

    #API
    def connect(self, event_handler: Union[None, callable] = None ) -> bool:
        # dbgprint("connecting..."
        if not self.medium.connected:
            self.connected = self.medium.start_connection(self)

        if self.offset is None:
            self.offset = self.__ask_for_offset()
            # dbgprint(f"offset device {self.offset}")

        if self.uses_socket and self.__eventlistener is None:
            if event_handler is not None:
                self.__event_handler = event_handler

            if self.__event_handler is None:
                raise ValueError('configure an event_hanler')

            self.__eventlistener = Thread(target=receive_events, args=(self, self.medium, self.__event_handler), daemon=True)
            self.__eventlistener.start()

        return self.connected

    def run(self) -> bool:
        run_msg = AMessage(Interrupts['run'] + '\n', receive_run_ack)
        return self.medium.send(run_msg)

    def pause(self):
        pause_msg = AMessage(Interrupts['pause'] + '\n', receive_ack_pause)
        return self.medium.send(pause_msg)



    def step(self, amount = 1):
        msgs = []
        for _ in range(amount):
            step_msg = AMessage(Interrupts['step'] + '\n', receive_step_ack)
            msgs.append(step_msg)
        return self.medium.send(msgs)

    def remove_breakpoint(self, addr: int) -> bool:
        (size_hex, addr_hex) = bp_addr_helper(self.offset, addr)
        content = Interrupts['rmvbp'] + size_hex[2:] + addr_hex[2:] + '\n'
        rmbp_msg = AMessage(content.upper(), receive_rmvbp)
        return self.medium.send(rmbp_msg)

    def add_breakpoint(self, addr: int) -> bool:
        # dbgprint(f'addr {addr} offset {self.offset}')
        (size_hex, addr_hex) = bp_addr_helper(self.offset, addr)
        content = Interrupts['addbp'] + size_hex[2:] + addr_hex[2:] + '\n'
        addbp_msg = AMessage(content.upper(), receive_addbp)

        return self.medium.send(addbp_msg)

    def halt(self, state):
        raise NotImplementedError

    def upload(self, wasm: bytes, config: dict) -> None:
        global proxy_config
        proxy_config = config

        interrupt = Interrupts['updateModule']
        ask4commit = AMessage(interrupt + '\n', receive_ack)
        sers = encoder.serialize_wasm(interrupt, wasm, self.max_bytes)

        l = len(sers)
        msgs = [ask4commit]
        for idx, content in enumerate(sers):
            rpl = receive_uploaddone if (idx + 1) == l else receive_ack
            dbgprint(f'#{len(content) + 1} Content {content}')
            msgs.append(
                AMessage(content + '\n',  rpl))
        for m in msgs:
            self.medium.send(m)

    def send_proxies(self, config: dict) -> None:
        lst = config['proxy']
        h = config['host']
        p = config['port']

        sers = encoder.serialize_proxies(Interrupts['recvproxies'], h, p, lst, self.max_bytes)
        msgs = []
        for i, s in enumerate(sers):
            rpl =  receive_done if (i + 1) == len(sers) else receive_ack
            m  = AMessage(s + '\n', rpl)
            msgs.append(m)

        for m in msgs:
            self.medium.send(m)

    def commit(self, wasm) -> bool:
        interrupt = Interrupts['updateModule']
        ask4commit = AMessage(interrupt + '\n', receive_ack)
        sers = encoder.serialize_wasm(interrupt, wasm, self.max_bytes)

        l = len(sers)
        msgs = [ask4commit]
        for idx, content in enumerate(sers):
            rpl = receive_commitdone if (idx + 1) == l else receive_ack
            dbgprint(f'#{len(content) + 1} Content {content}')
            msgs.append(
                AMessage(content + '\n',  rpl))

        replies = self.medium.send(msgs)
        succ = replies[-1]
        if succ:
            self.offset = self.__ask_for_offset()
            dbgprint(f"new offset post commit {self.offset}")

        return succ


    def get_execution_state(self):
        dump_msg = AMessage(Interrupts['dump'] + '\n', receive_dump)
        _dumpjson = self.medium.send(dump_msg)
        dbgprint(f'the dumpjson {_dumpjson}')
        if self.offset != _dumpjson['start'][0]:
            dbgprint('new offset')
            self.offset = _dumpjson['start'][0]

        return wood_state_to_wa_state(_dumpjson)


    # Helper methods
    def has_offset(self):
        return self.offset is not None

    @property
    def offset(self):
        return self.__offset

    @offset.setter
    def offset(self, off):
        self.__offset = off

    def clear_offset(self):
        self.offset = None

    def stopEventThread(self):
        self.__eventlistener = None

    def receive_session(self, session: dict) -> bool:
        recv_int = Interrupts['receivesession']
        wood_state = wa_state_to_wood_state(session, self.offset)
        # print(f'state to send to wood {wood_state}')
        dbgprint(f"State to send {wood_state}")
        sers = encoder.serialize_session(wood_state, recv_int, self.max_bytes)
        msgs = []
        l = len(sers)
        assert l >= 2, f'at least two expected got {l}'
        for idx, content in enumerate(sers):
            rpl = receive_done_session if (idx + 1) == l else receive_ack
            msgs.append(AMessage(content + '\n', rpl))

        dbgprint(f"about to send #{len(msgs)}")
        replies = self.medium.send(msgs)
        return replies[-1]

    def step_until(self, addr: str) ->  None:
        dbgprint(f'stepping until addr {addr} offset {self.offset}')
        (size_hex, addr_hex) = bp_addr_helper(self.offset, addr)
        content = Interrupts['until'] + size_hex[2:] + addr_hex[2:] + '\n'
        msg = AMessage(content.upper(), receive_until_ack)
        return self.medium.send(msg)

    def update_offset(self) -> None:
        newoff = self.__ask_for_offset()
        dbgprint(f'updating offset old_offset={self.offset} new offset={newoff}')
        self.offset = newoff
        
    #private
    def __ask_for_offset(self) -> str:
        offmsg = AMessage(Interrupts['offset'] + '\n', receive_offset)
        off = self.medium.send(offmsg)
        return off

# receive socket content functions
def receive_events(wood: WOODManager, aMedium: AMedium, callback: callable) -> None:
    import time #TODO remove
    at_start = b'AT '
    at_end = b'!\n'
    err_start = b'{"error":'
    err_end = b'}\n'
    timeout = float(0.1)
    while True:
        if not aMedium.has_event(timeout):
            continue

        #input has been received
        _start = aMedium.recv_until([at_start, err_start], event=True)
        _end = aMedium.recv_until([at_end, err_end], event = True)

        if not aMedium.connected:
            wood.connected = False
            callback({'event': 'disconnection'})
            break

        if _start.find(at_start) >= 0:
            _bp = _end[:-len(at_end)].decode()
            bp = hex(int(_bp , 16) - int(wood.offset, 16))
            callback({'event': 'at bp', 'breakpoint': bp})
        else:
            start = time.monotonic()
            _dump = receive_dump(wood, aMedium, ignore_prev_hash = False)
            if _dump is None:
                continue
            _bytes = err_start + _end[:-len(b'\n')]
            _obj = json.loads(_bytes.decode())
            _event = {
                'event': 'error',
                'msg': _obj['error'],
                'start_time': start,
                'time':time
            }
            _dump['session_size'] = _dump['session_size'] + len(_bytes) # TODO remove
            _event['execution_state'] = wood_state_to_wa_state(_dump)
            callback(_event)

    dbgprint("stopping event thread")
    wood.stopEventThread()

def receive_offset(wood, aMedium) -> str:
    end = b'"}"\n'
    _noise = aMedium.recv_until(b'"offset":"')
    byts = aMedium.recv_until(end)[:-len(end)]
    return byts.decode()


def receive_initstep_run(_, sock):
    sock.recv_until(AnsProtocol['run'].encode())
    return True

def receive_run_ack(_, sock):
    sock.recv_until(AnsProtocol['run'].encode())
    return True

def receive_ack_pause(_, sock):
    sock.recv_until(AnsProtocol['pause'].encode())
    return True

def receive_step_ack(wood: WOODManager, medium: AMedium) -> bool:
    medium.recv_until(AnsProtocol['step'].encode())
    medium.recv_until(b'STEP DONE!\n', wait = True, timeout=True)
    dbgprint("step done")
    return True

def receive_dump(wood: WOODManager, aMedium: AMedium, ignore_prev_hash = True):
    dump_json = receive_dump_helper(aMedium, ignore_prev_hash)
    return dump_json


# def receive_locals(wood: wood, aMedium: AMedium):
#     loc_json = receive_locals_helper(aMedium)
#     return loc_json

# def receive_locals_helper(aMedium: AMedium):
#     loc_end = b'\n'
#     _noise = aMedium.recv_until(b'STACK')
#     byts = aMedium.recv_until(loc_end)[:-len(loc_end)]
#     parsed = json.loads(byts)
#     return parsed

def receive_rmvbp(wood, aMedium) -> bool:
    dbgprint("receive rmvbp")
    bp_end = b'!\n'
    _ = aMedium.recv_until(b'BP ')
    bp_bytes = aMedium.recv_until(bp_end)[:-len(bp_end)]
    dbgprint(f"removed bp {bp_bytes.decode()}")
    return True

def receive_addbp(wood, aMedium) -> bool:
    # dbgprint("receive addbp")
    bp_end = b'!\n'
    _ = aMedium.recv_until(b'BP ')
    bp_bytes = aMedium.recv_until(bp_end)[:-len(bp_end)]
    return True

def receive_until_ack(wood, aMedium) -> bool:
    dbgprint("receive until pc")
    bp_end = b'!\n'
    _ = aMedium.recv_until(b'Until ')
    bp_bytes = aMedium.recv_until(bp_end)[:-len(bp_end)]
    dbgprint(f"ack until pc {bp_bytes.decode()}")
    aMedium.recv_until(b'STEP DONE!\n')
    return True

def receive_commitdone(wood, aSocket) -> bool:
    aSocket.recv_until(until=b'restart done!\n')
    dbgprint("received commit done")
    return True

def receive_ack(wood, aMedium) -> bool:
    aMedium.recv_until(until=b'ack!\n')
    return True

def receive_done(wood, aMedium) -> bool:
    aMedium.recv_until(until=b'done!\n')
    return True

def receive_done_session(wood, aMedium) -> bool:
    aMedium.recv_until(until=b'done!\n')
    dbgprint("done receiving sessions")
    return True

def receive_uploaddone(wood, aMedium):
    global proxy_config 
    # aMedium.recv_until(until=b'done!\n') #incorrect
    aMedium.recv_until(until=b'restart done!\n')
    wood.send_proxies(proxy_config)
    proxy_config = None

def bytes2int(data):
    ints = []
    for i in range(0, len(data), 4):
        x = int.from_bytes(data[i:i+4],  'little', signed=False)
        ints.append(x)
    return ints

# receive helper functions

prev_h = 3
def receive_dump_helper(sock, ignore_prev_hash = True):
    global prev_h

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
        print(f"failed for raw {json_bytes}")
        raise ValueError("something wrong")


    if not ignore_prev_hash:
        h = hash(json_bytes)
        if prev_h == h:
            dbgprint("Ignoring Received session")
            return None
        prev_h = h

    dbgprint(f'bytes {dec}')
    parsed = json.loads(dec)
    parsed['memory']['bytes'] = membytes
    parsed['table']['elements'] = bytes2int(elements)
    br_tbl = parsed['br_table']
    br_tbl['size'] = int(br_tbl['size'], 16)
    br_tbl['labels'] = bytes2int(labels)
    parsed['session_size'] = len(json_bytes) # TODO remove
    return parsed

def bp_addr_helper(offset, code_addr):
    all_bp_addr = util.sum_hexs([offset, code_addr])  # remove '0x'
    bp_addr = all_bp_addr
    if len(all_bp_addr[2:]) % 2 != 0:
        missing_chars = len(all_bp_addr[2:]) % 2
        bp_addr = "0x" + ( missing_chars * '0') + all_bp_addr[2:]

    amount_bytes = int(len(bp_addr[2:]) / 2)
    _hex = hex(amount_bytes)
    if int(_hex[2:], 16) < 16:
        _hex = '0x0' + _hex[2:]
    return (_hex, bp_addr)

def old_bp_addr_helper(offset, code_addr):
    bp_addr = util.sum_hexs([offset, code_addr])  # remove '0x'
    amount_chars = math.floor(len(bp_addr[2:]) / 2)
    if amount_chars % 2 != 0:
        dbgprint("WARNING: breakpoint address is not even addr")
        dbgprint(
            f"offset {offset} code_addr {code_addr} chars {amount_chars} calculated addr: {bp_addr}")
    else:
        pass

    _hex = hex(amount_chars)
    if int(_hex[2:], 16) < 16:
        _hex = '0x0' + _hex[2:]
    return (_hex, bp_addr)
def wood_state_to_wa_state(dump_json: dict) -> dict:
    offset = int(dump_json['start'][0], 16)
    state = {}
    state['pc'] = hex( int(dump_json['pc'], 16) - offset)
    if dump_json.get('pc_error', None) is not None:
        state['pc_error'] = hex( int(dump_json['pc_error'], 16) - offset)

    state['breakpoints'] = [  hex( int(b, 16) - offset) for b in dump_json['breakpoints']]
    state['table'] = {
        'max': dump_json['table']['max'],
        'min': dump_json['table']['init'],
        'elements': dump_json['table']['elements']
    }
    state['memory'] = {
        'pages': dump_json['memory']['pages'],
        'min': dump_json['memory']['init'],
        'max': dump_json['memory']['max'],
        'bytes': dump_json['memory']['bytes'],
    }
    state['br_table'] = dump_json['br_table']['labels']
    state['globals'] = dump_json['globals']
    state['stack'] =  [s for s in dump_json['stack']]
    state['session_size'] = dump_json['session_size'] #TODO remove

    _frame_types = {
        0: 'fun',
        1: 'init_exp',
        2: 'block',
        3: 'loop',
        4: 'if'
    }

    _cs = []
    for frame in dump_json['callstack']:
        cleaned_frame = {
            'block_type': _frame_types[frame['type']],
            'sp': frame['sp'],
            'fp': frame['fp'],
            'ret_addr': hex(int(frame['ra'], 16) - offset),
        }
        if cleaned_frame['block_type'] == 'fun':
            cleaned_frame['fidx'] = int(frame['fidx'], 16)
        else:
            cleaned_frame['block_key'] = hex( int(frame['block_key'], 16) - offset)
        _cs.append(cleaned_frame)

    state['callstack'] = _cs
    return state


def wa_state_to_wood_state(_json: dict, offset: str) -> dict:
    _offset = int(offset, 16)
    rebase = lambda addr : hex( int(addr, 16) + _offset)
    _pc_error = _json['pc_error']
    if isinstance(_pc_error, str): 
       _pc_error = rebase(_pc_error) 
    elif isinstance(_pc_error, int):
       _pc_error = hex(_pc_error + _offset)

    state = {
        'pc' : rebase(_json['pc']),
        'pc_error': _pc_error,
        'breakpoints': [rebase(bp) for bp in _json['breakpoints']],
        'br_table': {
            'size': len(_json['br_table']),
            'labels': _json['br_table'],
            },
        'globals': _json['globals'],
        'table': {
            'init': _json['table'].get('min', 0),
            'max': _json['table'].get('max', 0),
            'elements' : _json['table']['elements']
        },
        'memory': {
            'init': _json['memory'].get('min', 0),
            'max': _json['memory'].get('max', 0),
            'pages': _json['memory']['pages'],
            'bytes': _json['memory']['bytes'],
        },
        'stack': _json['stack'],
    }

    _frame_types = {
        'fun': 0,
        'init_exp': 1,
        'block': 2,
        'loop': 3,
        'if': 4
    }

    callstack = []
    for frame in _json['callstack']:
        _f = {
            'idx' : frame['idx'],
            'type': _frame_types[frame['block_type']],
            'fidx': hex(frame.get('fidx', 0)),
            'sp': frame['sp'],
            'fp': frame['fp'],
            'ra': frame.get('ret_addr', ''),
            'block_key': frame.get('block_key', '')
        }
        if frame.get('ret_addr', False):
            _f['ra'] = rebase(frame['ret_addr'])
        if frame.get('block_key', False):
            _f['block_key'] = rebase(frame['block_key'])
        callstack.append(_f)

    callstack.sort(key = lambda f: f['idx'], reverse= False)
    state['callstack'] = callstack

    return state
