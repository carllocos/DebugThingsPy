import math
import json

from serializers import serializer_interface as interf
from communication import protocol as ptc
from boards import warduino_msg as msgs
from utils import util


class Serializer(interf.ASerial):

    def __init__(self):
        super().__init__()
        self.__current_bp = False
        self.__dumps = []
        self.__breakpoints = []
        self.__locals = []
        self.__debugger = False

    def set_debugger(self, debugger):
        self.__debugger = debugger

    def has_stack_for(self, bp):
        with_off = util.sum_hexs([bp, self.__offset])
        return next( (d for d in self.__dumps if d['bp'] == with_off) , False) and True

    def initialize_step(self, state):
        return [msgs.FirstMsg(), msgs.RunMsg()]

    def halt(self, state):
        return [msgs.HaltMsg()]

    def run(self, state):
        return [msgs.RunMsg()]

    def pause(self, state):
        return [msgs.PauseMsgs()]

    def step(self, state):
        return [msgs.StepMsg()]

    def ack_add_bp(self, bp):
        #print(f'adding bp: {bp}')
        self.__breakpoints.append(bp)

    def ack_rmv_bp(self, bp):
        #print(f'deleting bp: {bp}')
        self.__breakpoints = [ p for p in self.__breakpoints if p != bp]

    def add_breakpoint(self, state):
        _code = state.code_info()
        (_size, _bp_addr) = bp_addr(self.__offset, _code.hex_addr())
        _msg = msgs.AddBreakPointMsg(_size, _bp_addr)

        return [_msg]

    def remove_breakpoint(self, state):
        _code = state.code_info()
        (_size, _bp_addr) = bp_addr(self.__offset, _code.hex_addr())
        _msg = msgs.RemoveBreakPointMsg(_size, _bp_addr)

        return [_msg]

    def callstack_msgs(self, state):
        _dm = msgs.DumpMsg()
        return [_dm, msgs.DumpLocals(_dm)]

    def get_callstack(self, bp):
        with_off = util.sum_hexs([bp, self.__offset])
        _dump = next( (d for d in self.__dumps if d['bp'] == with_off), False)
        _locals = next( (l for l in self.__locals if l['bp'] == with_off), False)
        if not _dump and not _locals:
            return False

        return (bp, _dump, _locals)

    def set_offset(self, off):
        self.__offset = off

    def get_offset(self):
        return self.__offset

    def current_bp(self, bp):
        self.__current_bp = bp

    def add_dump(self, dump):
        self.__dumps.append({'dump': dump, 'bp': self.__current_bp})

    def add_local_dump(self, local_dump):
        self.__locals.append({'local_dump': local_dump, 'bp': self.__current_bp})

    def process_answer(self, msg):
        if msgs.is_first_msg(msg):
            process_first_msg(self, msg)
            return
        if msgs.is_run_msg(msg):
            process_run_msg(msg)
            return
        if msgs.is_halt_msg(msg):
            process_halt_msg(msg)
            return
        if msgs.is_add_bp_msg(msg):
            process_add_bp(self, self.__debugger, msg)
            return
        if msgs.is_rmv_bp_msg(msg):
            process_rmv_bp(self, self.__debugger, msg)
            return
        if msgs.is_at_bp_msg(msg):
            process_at_bp_msg(self, self.__debugger, msg)
            return
        if msgs.is_dump_msg(msg):
            process_dump(self, msg)
            return
        if msgs.is_local_dump(msg):
            process_dump_local(self, msg)
            return
        print(f'received unhandled message {msg.NAME} {msg.answer}')
#####################################################################################################################################################
#####################################################################################################################################################
#### HELP FUNCTIONS
#####################################################################################################################################################
#####################################################################################################################################################
def process_first_msg(serializer, msg):
    ans = msg.answer
    try:
        all_bytes = ans['end']
        no_noise_answ = all_bytes[:-len(msg.end)]
        parsed = json.loads(no_noise_answ)
        offset = parsed['start'][0]
        serializer.set_offset(offset)
        #print(f'set offset {offset}')
    except:
        print('first message could not be parsed')
        print(f'received {ans}')

def process_dump_local(encoder, msg):
    ans = msg.answer
    try:
        all_bytes = ans['end']
        no_noise_answ = all_bytes[:-len(msg.end)]
        parsed = json.loads(no_noise_answ)
        encoder.add_local_dump(parsed)
        #print(f'parsed local dump {parsed}')
    except:
        print(f'Ans {msg.NAME} could not be parsed')
        print(f'received {ans}')

def process_dump(encoder, msg):
    ans = msg.answer
    try:
        all_bytes = ans['end']
        no_noise_answ = all_bytes[:-len(msg.end)]
        parsed = json.loads(no_noise_answ)
        encoder.add_dump(parsed)
        #print(f'parsed dump {parsed}')
    except:
        print('first message could not be parsed')
        print(f'received {ans}')

def process_add_bp(encoder, debugger, msg):
    #print(f'BP ADDED answer: {msg.answer}')
    encoder.ack_add_bp(msg.bp_addr)
    no_off = util.substract_hexs([msg.bp_addr, encoder.get_offset()])
    debugger.ack_add_bp(no_off)

def process_rmv_bp(encoder, debugger, msg):
    #print(f'BP REMOVED answer: {msg.answer}')
    encoder.ack_rmv_bp(msg.bp_addr)
    no_off = util.substract_hexs([msg.bp_addr, encoder.get_offset()])
    debugger.ack_rmv_bp(no_off)

def process_at_bp_msg(encoder,debugger,  msg):
    #print(f'At BP answer: {msg.answer}')
    encoder.current_bp(msg.bp_addr)
    no_off = util.substract_hexs([msg.bp_addr, encoder.get_offset()])
    debugger.ack_current_bp(no_off)

def process_run_msg(msg):
    #print(f'received answer for run_msg: {msg.answer}')
    #print(f'device is running')
    return

def process_halt_msg(msg):
    #print(f'received answer for halt_msg: {msg.answer}')
    #print(f'device is halted')
    return

def bp_addr(offset, code_addr):
    bp_addr = util.sum_hexs([offset, code_addr]) #remove '0x'
    amount_chars = math.floor(len(bp_addr[2:]) / 2)
    if amount_chars % 2 != 0:
        print("WARNING: breakpoint address is not even addr")
        print(f"offset {offset} code_addr {code_addr} chars {amount_chars} calculated addr: {bp_addr}")

    _hex = hex(amount_chars)
    if int(_hex[2:], 16) < 16:
        _hex = '0x0' + _hex[2:]

    #print(f'tuple ({_hex}, {bp_addr})')
    return (_hex, bp_addr)
