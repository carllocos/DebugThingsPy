import math
import json
import struct as struct #https://www.delftstack.com/howto/python/how-to-convert-bytes-to-integers/
import inspect

from serializers import serializer_interface as interf
from communication import protocol as ptc
from boards import warduino_msg as msgs
from utils import util
from . import encoder as encEncoder

DEBUG = True

def dbgprint(s):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    cn =str(calframe[1][3])
    if DEBUG:# and cn in ONLY:
        print((cn + ':').upper(), s)

#TODO use builder associated to each protocol. Probably a dictionary extension
class Serializer(interf.ASerial):

    def __init__(self):
        super().__init__()
        self.__current_bp = False
        self.__dumps = []
        self.__breakpoints = []
        self.__locals = []
        self.__debugger = False
        self.__temp = []
        self.__bytes = []
        self.__offset = False

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
        ##print(f'adding bp: {bp}')
        self.__breakpoints.append(bp)

    def ack_rmv_bp(self, bp):
        ##print(f'deleting bp: {bp}')
        self.__breakpoints = [ p for p in self.__breakpoints if p != bp]

    def add_breakpoint(self, state, wait_for_at = True):
        _code = state.code_info()
        (_size, _bp_addr) = bp_addr(self.__offset, _code.hex_addr())
        _msg = msgs.AddBreakPointMsg(_size, _bp_addr, wait_for_at)

        return [_msg]

    def at_msg(self, state):
        _code = state.code_info()
        (_size, _bp_addr) = bp_addr(self.__offset, _code.hex_addr())
        _msg = msgs.ForReceive(msgs.AtBP(_bp_addr))
        #  print(f"Message AT {_msg}")

        return [_msg]

    def dummy_add_bp(self, h, off = None):
        if off is not None:
            self.__dumy_offset = off
        (_size, _bp_addr) = bp_addr(self.__dumy_offset , h)
        return msgs.AddBreakPointMsg.print_str(_size, _bp_addr)

    def dummy_sub_bp(self, h, off=None):
        if off is  None:
            off = self.__dumy_offset
        return hex(int(h, 16) - int(off, 16))

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

    def has_offset(self):
        return self.__offset

    def set_offset(self, off):
        self.__offset = off

    def append_temp(self, temp):
        self.__temp.append(temp)

    def append_bytes(self, b):
        self.__bytes.append(b)

    def clean_temp(self):
        self.__temp = []

    def clean_bytes(self):
        self.__bytes = []

    def get_temp(self):
        return self.__temp

    def get_bytes(self):
        return self.__bytes

    def get_offset(self):
        return self.__offset

    def current_bp(self, bp):
        self.__current_bp = bp

    def add_dump(self, dump):
        self.__dumps.append({'dump': dump, 'bp': self.__current_bp})

    def add_local_dump(self, local_dump):
        self.__locals.append({'local_dump': local_dump, 'bp': self.__current_bp})

    def clean_session(self, dump, vals, new_offset):
        dbgprint('cleaning session')
        return encEncoder.clean_session(dump, vals, new_offset)

    def process_answer(self, msg):
        if msgs.is_first_msg(msg):
            process_first_msg(self, msg)
            return
        elif msgs.is_table_bytes(msg):
            process_table_bytes(self, msg)
            return
        elif msgs.is_rest_dump(msg):
            process_rest_dump(self, msg)
            return
        elif msgs.is_linmem(msg):
            process_linmen(self, msg)
            return
        elif msgs.is_second_rest_dump(msg):
            process_rest_dump(self, msg)
            return
        elif msgs.is_brtable_bytes(msg):
            process_brtable_bytes(self, msg)
            return
        elif msgs.is_end_dump(msg):
            process_end_of_dump(self, msg)
            return
        elif msgs.is_run_msg(msg):
            process_run_msg(msg)
            return
        elif msgs.is_halt_msg(msg):
            process_halt_msg(msg)
            return
        elif msgs.is_add_bp_msg(msg):
            process_add_bp(self, self.__debugger, msg)
            return
        elif msgs.is_rmv_bp_msg(msg):
            process_rmv_bp(self, self.__debugger, msg)
            return
        elif msgs.is_at_bp_msg(msg):
            process_at_bp_msg(self, self.__debugger, msg)
            return
        elif msgs.is_dump_msg(msg):
            process_dump(self, msg)
            return
        elif msgs.is_local_dump(msg):
            process_dump_local(self, msg)
            return
        #  elif msgs.is_some_hex(msg):
        #      process_some_hex_element(self, msg)
        #      return
        #  elif msgs.is_some_end_dump(msg):
        #      process_some_end(self, msg)
        #      return
        #  elif msgs.is_opcode(msg):
        #      process_opcode(self, msg)
        #      return
        else:
            print(f'received unhandled message {msg.NAME} {msg.answer}')
#####################################################################################################################################################
#####################################################################################################################################################
#### HELP FUNCTIONS
#####################################################################################################################################################
#####################################################################################################################################################
#  def process_opcode(ser, msg):
#      print("RECEIVED ANSW OPCODE")
#      print(msg.answer)

def process_first_msg(serializer, msg):
    ans = msg.answer
    try:
        all_bytes = ans['end']
        no_noise_answ = all_bytes[:-len(msg.end)]
        serializer.append_temp(no_noise_answ)
    except:
        print('first message could not be parsed')
        print(f'received {ans}')

debug_on = False
def process_table_bytes(encoder, msg):
    global debug_on
    #  print("process_table_bytes")
    #  print(msg.answer)
    ans = msg.answer['end']
    ans = ans[:-len(msg.end)]

    debug_on = False
    elems = list(map(bytes_2_int, receive_bytes(ans)))
    #  print("Decoded hex")
    #  print(elems)
    debug_on = False
    encoder.append_bytes(elems)

def process_rest_dump(encoder,msg):
    #  #print('processings rest dump')
    #  #print(f'removing {msg.end}')
    #  #print(msg.answer)
    answ = msg.answer['end']
    answ = answ[:-len(msg.end)]
    #  #print(f'appending {answ}')
    encoder.append_temp(answ)
    #  #print('-------------------------------------')
    #  #print()

REC_MEM = False
def process_linmen(encoder, msg):
    global REC_MEM
    global debug_on
    debug_on = False
    REC_MEM = False
    if REC_MEM:
        print("process_linmen")
    #print(msg.answer)
    _ans = msg.answer['end'][:-len(msg.end)]
    _elems = receive_bytes(_ans, merge=True)
    encoder.append_bytes(_elems)

    #  print("Decoded hex")
    #  print(_elems)
    #  print("End DECODED HEX")
    debug_on = False

def process_brtable_bytes(encoder, msg):
    #print("process_brtable_bytes")
    #print(msg.answer)
    ans = msg.answer['end'][:-len(msg.end)]
    _elems = list(map(bytes_2_int, receive_bytes(ans)))
    encoder.append_bytes(_elems)
    #print("Decoded hex")
    #print(_elems)
    #print("End DECODED HEX")

def process_end_of_dump(encoder, msg):
    #print('process_end_of_dump')
    all_bytes = msg.answer['end'][:-len(msg.end)]
    #print(f'after removal {all_bytes}')
    encoder.append_temp(all_bytes)
    #print(f'all tempts {encoder.get_temp()}')
    _temps = False
    for i in encoder.get_temp():
        if not _temps:
            _temps = i
        else:
            _temps += i
    #print('TEMPPPPPPPP')
    #print(_temps)
    parsed = json.loads(_temps)
    encoder.clean_temp()
    offset = parsed['start'][0]
    #print("THE BYTES")
    #print(encoder.get_bytes())
    #print("_________")
    _bytes = encoder.get_bytes()
    tbl = parsed['table']
    tbl['elements'] = _bytes[0]
    _lm = parsed['memory']
    _lm['bytes']=_bytes[1]
    brtbl = parsed['br_table']
    brtbl['size'] = int(brtbl['size'], 16)
    brtbl['labels']= _bytes[2]
    encoder.clean_bytes()
    if not encoder.has_offset():
        encoder.set_offset(offset)
    else:
        encoder.add_dump(parsed)

    #  print("THE OPCODE")
    #  print(parsed['opcode'])
    #print("THE WHOLE THING")
    #print(parsed)

def process_dump_local(encoder, msg):
    ans = msg.answer
    try:
        all_bytes = ans['end']
        no_noise_answ = all_bytes[:-len(msg.end)]
        parsed = json.loads(no_noise_answ)
        encoder.add_local_dump(parsed)
        #  print(f'parsed local dump {parsed}')
    except:
        print(f'Ans {msg.NAME} could not be parsed')
        print(f'received {ans}')

def process_dump(encoder, msg):
    ans = msg.answer
    try:
        all_bytes = ans['end']
        no_noise_answ = all_bytes[:-len(msg.end)]
        encoder.append_temp(no_noise_answ)
    except:
        print('first message could not be parsed')
        print(f'received {ans}')

#  def process_some_hex_element(encoder, msg):
#      #print("process_some_hex_element")
#      #print(msg.answer)
#      _bytes = msg.answer['end'][:-len(msg.end)]
#      (amount, _ ) = struct.unpack('<HH', _bytes[0:4])
#      _bytes = _bytes[4:] #TODO maybe apply code below only if _total_elems > 0
#      encoder.append_bytes(_bytes)
#      #print("Decoded hex")
#      #print(_bytes)
#      #print(f'got total elements {amount}')


#  def process_some_end(encoder, msg):
#      all_bytes = msg.answer['end']
#      no_noise_answ = encoder.get_temp() + all_bytes[:-len(msg.end)]
#      parsed = json.loads(no_noise_answ)
#      tbl = parsed['table']
#      tbl['elements'] = encoder.get_bytes()
#      encoder.clean_bytes()
#      encoder.add_dump(parsed)
#      encoder.clean_temp()

def process_add_bp(encoder, debugger, msg):
    #  print(f'BP ADDED answer: {msg.answer}')
    encoder.ack_add_bp(msg.bp_addr)
    no_off = util.substract_hexs([msg.bp_addr, encoder.get_offset()])
    debugger.ack_add_bp(no_off)

def process_rmv_bp(encoder, debugger, msg):
    #  print(f'BP REMOVED answer: {msg.answer}')
    encoder.ack_rmv_bp(msg.bp_addr)
    no_off = util.substract_hexs([msg.bp_addr, encoder.get_offset()])
    debugger.ack_rmv_bp(no_off)

def process_at_bp_msg(encoder,debugger,  msg):
    #  print(f'At BP answer: {msg.answer}')
    encoder.current_bp(msg.bp_addr)
    #  print(f"substract_hexs with {msg.bp_addr} and offset {encoder.get_offset()}")
    no_off = util.substract_hexs([msg.bp_addr, encoder.get_offset()])
    debugger.ack_current_bp(no_off)

def process_run_msg(msg):
    #print(f'received answer for run_msg: {msg.answer}')
    print(f'device is running')
    return

def process_halt_msg(msg):
    print(f'received answer for halt_msg: {msg.answer}')
    ##print(f'device is halted')
    return

def bp_addr(offset, code_addr):
    bp_addr = util.sum_hexs([offset, code_addr]) #remove '0x'
    amount_chars = math.floor(len(bp_addr[2:]) / 2)
    if amount_chars % 2 != 0:
        print("WARNING: breakpoint address is not even addr")
        print(f"offset {offset} code_addr {code_addr} chars {amount_chars} calculated addr: {bp_addr}")
    else:
        #  print("okay")
        pass

    _hex = hex(amount_chars)
    if int(_hex[2:], 16) < 16:
        _hex = '0x0' + _hex[2:]

    ##print(f'tuple ({_hex}, {bp_addr})')
    return (_hex, bp_addr)

def bytes_2_int(b):
    (fix, _) = struct.unpack('<HH', b)
    return fix

def receive_bytes(_bytes, merge = False):
    if debug_on:
        print("RECEIVE BYTES")
    (_total_elems, _ ) = struct.unpack('<HH', _bytes[0:4])
    _bytes = _bytes[4:] #TODO maybe apply code below only if _total_elems > 0
    (_bytes_per_elemnt, _ ) = struct.unpack('<HH', _bytes[0:4])
    _bytes = _bytes[4:]
    if debug_on:
        print(f'TOTAL ELEMS {_total_elems} BYTES/EL {_bytes_per_elemnt}')
    elems = []
    if merge:
        elems = _bytes
    else:
        for i in range(_total_elems):
            off = i * _bytes_per_elemnt
            _b = _bytes[off : off + _bytes_per_elemnt]
            elems.append(_b)
    return elems
