import sys
import inspect
import json
from threading import Thread
import math
import select
# import re
import struct

from interfaces import ASerial, AMessage, AMedium
from utils import util
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
    'updateModule' : '24',
}

DEBUG = False

def dbgprint(s):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    cn = str(calframe[1][3])
    if DEBUG:  # and cn in ONLY:
        print((cn + ':').upper(), s)


def errprint(s):
    print(s)
    sys.exit()


proxy_config = None

class WARDuino(ASerial):
    def __init__(self):
        super().__init__()
        self.__offset = None
        self.__dbg = None
        self.__eventThread = None
        self.__current_bp = None
        self.__dumps = []
        self.__locals = []
        self.__max_bytes = 100  # FIXME at 20 get issue due to pc_serialization
        self.__stepdump = None
        self.__stemplocals = None
        self.__medium = None
        self.__redirectdbg = None
        self.__connected = False
        self.__eventlistener = None
        #  self.__breakpoints = []
        #  self.__temp = []
        #  self.__bytes = []

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
        dbgprint(f"The dump {d}")
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
        offmsg = AMessage(Interrupts['offset'] + '\n', receive_offset)
        if not self.medium.connected:
            self.medium.start_connection(self)
        self.medium.send(offmsg)
        return self.connected


    def ask_for_offset(self) -> bool:
        offmsg = AMessage(Interrupts['offset'] + '\n', receive_offset)
        self.medium.send(offmsg)

    def run(self):
        run_msg = AMessage(Interrupts['run'] + '\n', receive_run_ack)
        self.medium.send(run_msg)

    def pause(self, state):
        raise NotImplementedError

    def step(self, amount = 1):
        dbgprint('generating callstack_msgs')
        msgs = []
        for _ in range(amount):
            step_msg = AMessage(Interrupts['step'] + '\n', receive_stepack)
            msgs.append(step_msg)
        msgs.append(AMessage(Interrupts['dump'] + '\n', receive_stepdump))
        msgs.append(AMessage(Interrupts['locals'] + '\n', receive_steplocals))
        self.medium.send(msgs)

    def remove_breakpoint(self, addr: int) -> None:
        (size_hex, addr_hex) = bp_addr_helper(self.offset, addr)
        content = Interrupts['rmvbp'] + size_hex[2:] + addr_hex[2:] + '\n'
        rmbp_msg = AMessage(content.upper(), receive_rmvbp)
        self.medium.send(rmbp_msg)

    def add_breakpoint(self, addr: int) -> bool:
        dbgprint(f'addr {addr} offset {self.offset}')
        (size_hex, addr_hex) = bp_addr_helper(self.offset, addr)
        content = Interrupts['addbp'] + size_hex[2:] + addr_hex[2:] + '\n'
        addbp_msg = AMessage(content.upper(), receive_addbp)

        if self.uses_socket:
            if self.__eventlistener is None:
                self.__eventlistener = Thread(target=receive_atbp, args=(self, self.medium))
                self.__eventlistener.start()
        self.medium.send(addbp_msg)

    def add_breakpoint_test(self, addr: str, with_offset: bool) -> bool:
        dbgprint(f'addr {addr}')
        off = self.offset if with_offset else 0
        (size_hex, addr_hex) = bp_addr_helper(off, addr)
        content = Interrupts['addbp'] + size_hex[2:] + addr_hex[2:] + '\n'
        addbp_msg = AMessage(content.upper(), receive_addbp)
        if self.uses_socket:
            if self.__eventlistener is None:
                self.__eventlistener = Thread(target=receive_atbp, args=(self, self.medium))
                self.__eventlistener.start()

        self.medium.send(addbp_msg)

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

    def debug_session(self):
        dbgprint('generating callstack_msgs')
        dump_msg = AMessage(Interrupts['dump'] + '\n', receive_dump)
        locs_msg = AMessage(Interrupts['locals'] + '\n', receive_locals)
        self.medium.send([dump_msg, locs_msg])

    # Helper methods
    def has_offset(self):
        return self.offset is not None

    @property
    def offset(self):
        return self.__offset

    @offset.setter
    def offset(self, off):
        dbgprint(f'local device new offset {off}')
        self.__offset = off

    def clear_offset(self):
        self.offset = None

    def stopEventThread(self):
        self.__eventThread = None

    def add_dump(self, dump):
        self.__dumps.append({'dump': dump, 'bp': self.__current_bp})

    def pop_callstack(self, bp):
        d = None
        s = None
        new_dumps = []
        new_locs = []
        assert len(self.__dumps) == len(self.__locals), 'not same length'
        for i in range(len(self.__dumps)):
            _dump = self.__dumps[i]
            _locs = self.__locals[i]

            if _dump['bp'] == bp:
                d = _dump
            else:
                new_dumps.append(_dump)

            if _locs['bp'] == bp:
                s = _locs
            else:
                new_locs.append(_locs)

        assert d is not None
        assert s is not None
        self.__locals = new_locs
        self.__dumps = new_dumps
        return (d, s)

    def add_local_dump(self, local_dump):
        self.__locals.append(
            {'local_dump': local_dump, 'bp': self.__current_bp})

    def add_stepdump(self, d):
        self.__stepdump = d

    def add_steplocals(self, l):
        self.__stemplocals = l

    def current_bp(self, bp):
        self.__current_bp = bp
        no_off = util.substract_hexs([bp, self.__offset])
        self.debugger.ack_current_bp(no_off)

    def force_cbp(self, cbp):
        self.__current_bp = cbp

    def has_stack_for(self, bp):
        if bp == 'specialbp':
            return False

        with_off = util.sum_hexs([bp, self.__offset])
        return next((d for d in self.__dumps if d['bp'] == with_off), False) and True

    def get_callstack(self, bp):
        with_off = util.sum_hexs([bp, self.__offset])
        _dump = next((d for d in self.__dumps if d['bp'] == with_off), False)
        _locals = next(
            (l for l in self.__locals if l['bp'] == with_off), False)
        if not _dump and not _locals:
            return False
        return (bp, _dump, _locals)

    def specialbp(self):
        return 'specialbp'

    def clean_session(self, dump, vals, new_offset):
        dbgprint('cleaning session')
        return encoder.clean_session(dump, vals, new_offset)

    def receive_session(self, dssession):
        recv_int = Interrupts['receivesession']
        sers = encoder.serialize_session(dssession, recv_int, self.max_bytes)
        msgs = []
        l = len(sers)
        for idx, content in enumerate(sers):
            rpl = receive_done if (idx + 1) == l else receive_ack
            msgs.append(AMessage(content + '\n', rpl))

        self.medium.send(msgs)

    def sync_with(self, dummybp):
        (dump_obj, locs) = self.pop_callstack(dummybp)
        _d = dump_obj['dump']
        offset = _d['start'][0]
        self.offset = offset
        self.current_bp(_d['pc'])
        self.add_dump(_d)
        self.add_local_dump(locs['local_dump'])

# receive socket content functions
def receive_atbp(warduino, aMedium):
    at_start = b'AT '
    at_end = b'!\n'
    timeout = float(0.2)
    while True:
        if not aMedium.has_event(timeout):
            continue

        _noise = aMedium.recv_bytes(at_start, event=True)
        bp_bytes = aMedium.recv_bytes(at_end, event=True)[:-len(at_end)]
        bp = bp_bytes.decode()
        warduino.current_bp(bp)

def receive_offset(warduino, aMedium):
    end = b'"}"\n'
    _noise = aMedium.recv_bytes(b'"offset":"')
    byts = aMedium.recv_bytes(end)[:-len(end)]
    dbgprint(f'bytes {byts}')
    warduino.offset = byts.decode()
    # parsed = json.loads(byts)
    # warduino.offset = parsed['offset']
    warduino.connected = True


def receive_initstep_run(_, sock):
    sock.recv_bytes(AnsProtocol['run'].encode())
    return True


def receive_run_ack(_, sock):
    sock.recv_bytes(AnsProtocol['run'].encode())
    dbgprint("device running")
    return True

def receive_stepack(warduino: WARDuino, medium: AMedium):
    medium.recv_bytes(AnsProtocol['step'].encode())
    medium.recv_bytes(b'STEP DONE!\n')
    dbgprint("stepped!")

def receive_stepdump(aSerializer, sock):
    dump_json = receive_dump_helper(sock)
    aSerializer.add_stepdump(dump_json)


def receive_steplocals(aSerializer, sock):
    locals_json = receive_locals_helper(sock)
    aSerializer.add_steplocals(locals_json)


def receive_dump(aSerializer, sock):
    dump_json = receive_dump_helper(sock)
    if not aSerializer.has_offset():
        dbgprint("chaning only offset")
        offset = dump_json['start'][0]
        aSerializer.set_offset(offset)
    else:
        dbgprint("saving dump")
        aSerializer.add_dump(dump_json)


def receive_locals(aSerializer, sock):
    parsed = receive_locals_helper(sock)
    dbgprint(parsed)
    aSerializer.add_local_dump(parsed)
    return True


def receive_locals_helper(sock):
    loc_end = b'\n'
    _noise = sock.recv_bytes(b'STACK')
    byts = sock.recv_bytes(loc_end)[:-len(loc_end)]
    parsed = json.loads(byts)
    return parsed


def receive_rmvbp(aSerializer, sock):
    dbgprint("receive rmvbp")
    bp_end = b'!\n'
    _ = sock.recv_bytes(b'BP ')
    bp_bytes = sock.recv_bytes(bp_end)[:-len(bp_end)]
    dbgprint(f"removed bp {bp_bytes.decode()}")
    return True


def receive_addbp(aSerializer, sock):
    dbgprint("receive addbp")
    bp_end = b'!\n'
    _ = sock.recv_bytes(b'BP ')
    bp_bytes = sock.recv_bytes(bp_end)[:-len(bp_end)]
    dbgprint(f"added bp {bp_bytes.decode()}")
    return True



def receive_commitdone(warduino, aSocket):
    aSocket.recv_bytes(until=b'restart done!\n')
    dbgprint("received commit done")
    warduino.ask_for_offset()

def receive_ack(aSerializer, aSocket):
    aSocket.recv_bytes(until=b'ack!\n')
    dbgprint("received ack")
    return True


def receive_done(aSerializer, aSocket):
    aSocket.recv_bytes(until=b'done!\n')
    dbgprint("received done")

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

    dbgprint(parsed)

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

# def noisefree(strng):
#     return list( filter(lambda s : s != '', strng.split('\n')) )

# def process_unknown(byts, unknown):
#     dbgprint(f'received chars unknown msg {unknown}')

# def receive_raw_bytes(_bytes, merge = False):
#     (_total_elems, _ ) = struct.unpack('<HH', _bytes[0:4])
#     _bytes = _bytes[4:] #TODO maybe apply code below only if _total_elems > 0
#     (_bytes_per_elemnt, _ ) = struct.unpack('<HH', _bytes[0:4])
#     _bytes = _bytes[4:]
#     elems = []
#     if merge:
#         elems = _bytes
#     else:
#         for i in range(_total_elems):
#             off = i * _bytes_per_elemnt
#             _b = _bytes[off : off + _bytes_per_elemnt]
#             elems.append(_b)
#     return elems

# def bytes_2_int(b):
#     (fix, _) = struct.unpack('<HH', b)
#     return fix

    # def add_breakpoint(self, state, wait_for_at=True):
    #     _code = state.code_info()
    #     (size_hex, addr_hex) = bp_addr_helper(self.__offset, _code.hex_addr())
    #     content = Interrupts['addbp'] + size_hex[2:] + addr_hex[2:] + '\n'
    #     addbp_msg = AMessage(content.upper(), receive_addbp)

    #     evt = self.__eventThread
    #     if evt is None:
    #         med = self.__dbg.get_med()
    #         evt = threading.Thread(target=receive_atbp, args=(self, med))
    #         self.__eventThread = evt
    #         evt.start()

    #     return [addbp_msg]
    # def remove_breakpoint(self, state):
    #     _code = state.code_info()
    #     (size_hex, addr_hex) = bp_addr_helper(self.__offset, _code.hex_addr())
    #     content = Interrupts['rmvbp'] + size_hex[2:] + addr_hex[2:] + '\n'
    #     rmbp_msg = AMessage(content.upper(), receive_rmvbp)
    #     return [rmbp_msg]
