import sys
import inspect
import json
from threading import Thread
import math
import select
import struct

from interfaces import ASerial, AMessage, AMedium
from utils import util, dbgprint, errprint
from . import encoder

AnsProtocol = {
    'dump': '10',
    'locals': '11',
    'receivesession': '22',
    'rmvbp': '07',
    'run': 'GO!\n',
    'step': 'STEP!\n'
}


Interrupts = {
    'addbp': '06',
    'dump': '10',
    'offset': '0x23',
    'locals': '11',
    'receivesession': '22',
    'recvproxies': '25',
    'rmvbp': '07',
    'run': '01',
    'step': '04',
    'until': '05',
    'updateModule' : '24',
}

proxy_config = None

class WARDuino(ASerial):
    def __init__(self):
        super().__init__()
        self.__offset = None
        self.__dbg = None
        self.__eventThread = None
        # self.__current_bp = None
        self.__dumps = []
        self.__locals = []
        self.__max_bytes = 1024  # FIXME at 20 get issue due to pc_serialization
        self.__stepdump = None
        self.__stemplocals = None
        self.__medium = None
        self.__redirectdbg = None
        self.__connected = False
        self.__eventlistener = None

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
    def connected(self, c) -> None:
        self.__connected = c

    @property
    def step_state(self):
        d = self.__stepdump
        off = d['start'][0]
        pc  = util.substract_hexs([d['pc'], off  ])
        return (pc, {'dump': d}, {'local_dump': self.__stemplocals})

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

    #API
    def connect(self) -> bool:
        dbgprint("connecting...")
        if not self.medium.connected:
            self.connected = self.medium.start_connection(self)

        self.offset = self.__ask_for_offset()
        dbgprint(f"offset device {self.offset}")
        return self.connected

    def run(self) -> bool:
        run_msg = AMessage(Interrupts['run'] + '\n', receive_run_ack)
        return self.medium.send(run_msg)

    def pause(self, state):
        raise NotImplementedError

    def step(self, amount = 1):
        msgs = []
        for _ in range(amount):
            step_msg = AMessage(Interrupts['step'] + '\n', receive_step_ack)
            msgs.append(step_msg)
        self.medium.send(msgs)
        return self.get_execution_state()

    def remove_breakpoint(self, addr: int) -> bool:
        (size_hex, addr_hex) = bp_addr_helper(self.offset, addr)
        content = Interrupts['rmvbp'] + size_hex[2:] + addr_hex[2:] + '\n'
        rmbp_msg = AMessage(content.upper(), receive_rmvbp)
        return self.medium.send(rmbp_msg)

    def add_breakpoint(self, addr: int, callback: callable) -> bool:
        dbgprint(f'addr {addr} offset {self.offset}')
        (size_hex, addr_hex) = bp_addr_helper(self.offset, addr)
        content = Interrupts['addbp'] + size_hex[2:] + addr_hex[2:] + '\n'
        addbp_msg = AMessage(content.upper(), receive_addbp)

        if self.uses_socket:
            if self.__eventlistener is None:
                self.__eventlistener = Thread(target=receive_atbp, args=(self, self.medium, callback))
                self.__eventlistener.start()
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

    def commit(self, wasm):
        interrupt = Interrupts['updateModule']
        ask4commit = AMessage(interrupt + '\n', receive_ack)
        sers = encoder.serialize_wasm(interrupt, wasm, self.max_bytes)
        print(f'sers {sers}')

        l = len(sers)
        msgs = [ask4commit]
        for idx, content in enumerate(sers):
            rpl = receive_commitdone if (idx + 1) == l else receive_ack
            dbgprint(f'#{len(content) + 1} Content {content}')
            msgs.append(
                AMessage(content + '\n',  rpl))
        for m in msgs:
            self.medium.send(m)

    def get_execution_state(self):
        dump_msg = AMessage(Interrupts['dump'] + '\n', receive_dump)
        locs_msg = AMessage(Interrupts['locals'] + '\n', receive_locals)
        [_dumpjson, _locjson ] = self.medium.send([dump_msg, locs_msg])
        if self.offset != _dumpjson['start'][0]:
            dbgprint('new offset')
            self.offset = _dumpjson['start'][0]

        return warduino_state_to_wa_state(_dumpjson, _locjson)


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
        self.__eventThread = None

    # def pop_callstack(self, bp):
    #     d = None
    #     s = None
    #     new_dumps = []
    #     new_locs = []
    #     assert len(self.__dumps) == len(self.__locals), 'not same length'
    #     for i in range(len(self.__dumps)):
    #         _dump = self.__dumps[i]
    #         _locs = self.__locals[i]

    #         if _dump['bp'] == bp:
    #             d = _dump
    #         else:
    #             new_dumps.append(_dump)

    #         if _locs['bp'] == bp:
    #             s = _locs
    #         else:
    #             new_locs.append(_locs)

    #     assert d is not None
    #     assert s is not None
    #     self.__locals = new_locs
    #     self.__dumps = new_dumps
    #     return (d, s)


    def add_stepdump(self, d):
        self.__stepdump = d

    def add_steplocals(self, l):
        self.__stemplocals = l

    def has_stack_for(self, bp):
        if bp == 'specialbp':
            return False

        with_off = util.sum_hexs([bp, self.__offset])
        return next((d for d in self.__dumps if d['bp'] == with_off), False) and True

    def specialbp(self):
        return 'specialbp'

    def receive_session(self, session: dict) -> bool:
        recv_int = Interrupts['receivesession']
        warduino_state = wa_state_to_warduino_state(session, self.offset)
        sers = encoder.serialize_session(warduino_state, recv_int, self.max_bytes)
        msgs = []
        l = len(sers)
        for idx, content in enumerate(sers):
            rpl = receive_done if (idx + 1) == l else receive_ack
            msgs.append(AMessage(content + '\n', rpl))

        replies = self.medium.send(msgs)
        return replies[-1]

    def step_until(self, addr: str) ->  None:
        dbgprint(f'stepping until addr {addr} offset {self.offset}')
        (size_hex, addr_hex) = bp_addr_helper(self.offset, addr)
        content = Interrupts['until'] + size_hex[2:] + addr_hex[2:] + '\n'
        msg = AMessage(content.upper(), receive_until_ack)
        return self.medium.send(msg)

    #private
    def __ask_for_offset(self) -> str:
        offmsg = AMessage(Interrupts['offset'] + '\n', receive_offset)
        off = self.medium.send(offmsg)
        return off

# receive socket content functions
def receive_atbp(warduino, aMedium, callback: callable) -> None:
    at_start = b'AT '
    at_end = b'!\n'
    timeout = float(0.2)
    while True:
        if not aMedium.has_event(timeout):
            continue

        _noise = aMedium.recv_bytes(at_start, event=True)
        bp_bytes = aMedium.recv_bytes(at_end, event=True)[:-len(at_end)]
        bp = bp_bytes.decode()
        dbgprint(f'decoded bp {bp}')
        dbgprint(f'offset is {warduino.offset}')
        bp = hex(int(bp , 16) - int(warduino.offset, 16))
        callback(bp)
        # warduino.current_bp(bp)

def receive_offset(warduino, aMedium) -> str:
    end = b'"}"\n'
    _noise = aMedium.recv_bytes(b'"offset":"')
    byts = aMedium.recv_bytes(end)[:-len(end)]
    return byts.decode()


def receive_initstep_run(_, sock):
    sock.recv_bytes(AnsProtocol['run'].encode())
    return True

def receive_run_ack(_, sock):
    sock.recv_bytes(AnsProtocol['run'].encode())
    return True

def receive_step_ack(warduino: WARDuino, medium: AMedium) -> None:
    medium.recv_bytes(AnsProtocol['step'].encode())
    medium.recv_bytes(b'STEP DONE!\n')

# def receive_stepdump(aSerializer, sock):
#     dump_json = receive_dump_helper(sock)
#     aSerializer.add_stepdump(dump_json)

# def receive_steplocals(aSerializer, sock):
#     locals_json = receive_locals_helper(sock)
#     aSerializer.add_steplocals(locals_json)


def receive_dump(aSerializer, sock):
    dump_json = receive_dump_helper(sock)
    return dump_json


def receive_locals(aSerializer, sock):
    loc_json = receive_locals_helper(sock)
    return loc_json


def receive_locals_helper(sock):
    loc_end = b'\n'
    _noise = sock.recv_bytes(b'STACK')
    byts = sock.recv_bytes(loc_end)[:-len(loc_end)]
    parsed = json.loads(byts)
    return parsed

def receive_rmvbp(warduino, aMedium) -> bool:
    dbgprint("receive rmvbp")
    bp_end = b'!\n'
    _ = aMedium.recv_bytes(b'BP ')
    bp_bytes = aMedium.recv_bytes(bp_end)[:-len(bp_end)]
    dbgprint(f"removed bp {bp_bytes.decode()}")
    return True

def receive_addbp(warduino, aMedium) -> bool:
    dbgprint("receive addbp")
    bp_end = b'!\n'
    _ = aMedium.recv_bytes(b'BP ')
    bp_bytes = aMedium.recv_bytes(bp_end)[:-len(bp_end)]
    dbgprint(f"added bp {bp_bytes.decode()}")
    return True

def receive_until_ack(warduino, aMedium) -> bool:
    dbgprint("receive until pc")
    bp_end = b'!\n'
    _ = aMedium.recv_bytes(b'Until ')
    bp_bytes = aMedium.recv_bytes(bp_end)[:-len(bp_end)]
    dbgprint(f"ack until pc {bp_bytes.decode()}")
    aMedium.recv_bytes(b'STEP DONE!\n')
    return True

def receive_commitdone(warduino, aSocket):
    aSocket.recv_bytes(until=b'restart done!\n')
    dbgprint("received commit done")
    warduino.ask_for_offset()

def receive_ack(warduino, aMedium) -> bool:
    aMedium.recv_bytes(until=b'ack!\n')
    return True

def receive_done(warduino, aMedium) -> bool:
    aMedium.recv_bytes(until=b'done!\n')
    return True

def receive_uploaddone(warduino, aMedium):
    global proxy_config 
    aMedium.recv_bytes(until=b'done!\n')
    warduino.send_proxies(proxy_config)
    proxy_config = None

def bytes2int(data):
    ints = []
    for i in range(0, len(data), 4):
        x = int.from_bytes(data[i:i+4],  'little', signed=False)
        ints.append(x)
    return ints

# receive helper functions


def receive_dump_helper(sock):
    _noise = sock.recv_bytes(b'DUMP!\n')

    raw_end = b']}'
    re_len = len(raw_end)

    json_bytes = b''
    json_bytes += sock.recv_bytes(b'"elements":[') + raw_end
    elements = sock.recv_bytes(raw_end)[:-re_len]
    json_bytes += sock.recv_bytes(b'"bytes":[') + raw_end
    membytes = sock.recv_bytes(raw_end)[:-2]
    json_bytes += sock.recv_bytes(b'"labels":[') + raw_end
    labels = sock.recv_bytes(raw_end)[:-re_len]
    json_bytes += sock.recv_bytes(b'\n')[:-len(b'\n')]

    parsed = json.loads(json_bytes.decode())

    parsed['memory']['bytes'] = membytes

    parsed['table']['elements'] = bytes2int(elements)

    br_tbl = parsed['br_table']
    br_tbl['size'] = int(br_tbl['size'], 16)
    br_tbl['labels'] = bytes2int(labels)
    return parsed


def bp_addr_helper(offset, code_addr):
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

def warduino_state_to_wa_state(dump_json: dict, loc_json: dict) -> dict:
    offset = int(dump_json['start'][0], 16)
    state = {}
    state['pc'] = hex( int(dump_json['pc'], 16) - offset)
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
    state['stack'] =  [s for s in loc_json['stack']]

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


def wa_state_to_warduino_state(_json: dict, offset: str) -> dict:
    _offset = int(offset, 16)
    rebase = lambda addr : hex( int(addr, 16) + _offset)

    state = {
        'pc' : rebase(_json['pc']),
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