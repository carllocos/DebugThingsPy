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
        self.__current_dump = False
        self.__current_locals = False

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

    def get_callstack(self):
        return (self.__current_bp, self.__current_dump, self.__current_locals)

    def get_cached_stack(self):
        return (self.__current_bp, self.__current_dump, self.__current_locals)

    def set_offset(self, off):
        self.__offset = off

    def current_bp(self, bp):
        self.__current_bp = bp

    def current_dump(self, dump):
        self.__current_dump = dump

    def current_local_dump(self, local_dump):
        self.__current_locals = local_dump

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
            process_add_bp(msg)
            return
        if msgs.is_rmv_bp_msg(msg):
            process_rmv_bp(msg)
            return
        if msgs.is_at_bp_msg(msg):
            process_at_bp_msg(self, msg)
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
        print(f'set offset {offset}')
    except:
        print('first message could not be parsed')
        print(f'received {ans}')

def process_dump_local(encoder, msg):
    ans = msg.answer
    try:
        all_bytes = ans['end']
        no_noise_answ = all_bytes[:-len(msg.end)]
        parsed = json.loads(no_noise_answ)
        encoder.current_local_dump(parsed)
        print(f'parsed local dump {parsed}')
    except:
        print(f'Ans {msg.NAME} could not be parsed')
        print(f'received {ans}')

def process_dump(encoder, msg):
    ans = msg.answer
    try:
        all_bytes = ans['end']
        no_noise_answ = all_bytes[:-len(msg.end)]
        parsed = json.loads(no_noise_answ)
        encoder.current_dump(parsed)
        print(f'parsed dump {parsed}')
    except:
        print('first message could not be parsed')
        print(f'received {ans}')

def process_add_bp(msg):
    print(f'BP ADDED answer: {msg.answer}')

def process_rmv_bp(msg):
    print(f'BP REMOVED answer: {msg.answer}')

def process_at_bp_msg(encoder, msg):
    print(f'At BP answer: {msg.answer}')
    encoder.current_bp(msg.bp_addr)


def process_run_msg(msg):
    print(f'received answer for run_msg: {msg.answer}')
    print(f'device is running')

def process_halt_msg(msg):
    print(f'received answer for halt_msg: {msg.answer}')
    print(f'device is halted')
#  def process_first_msg(serializer, msg):
#      ans = msg.reply_template.answer
#      try:
#          parsed = json.loads(ans['end'])
#          offset = parsed['start'][0]
#          serializer.set_offset(offset)
#          print(f'set offset {offset}')
#      except:
#          print('first message could not be parsed')
#          print(f'received {ans}')

#  def process_add_bp(msg):
#      print(f'BP ADDED answer: {msg.reply_template.answer}')

#  def process_rmv_bp(msg):
#      print(f'BP REMOVED answer: {msg.reply_template.answer}')

#  def process_code_dump(msg):
#      pass

#  def process_run_msg(msg):
#      print(f'received answer for run_msg: {msg.reply_template.answer}')
#      print(f'device is running')

#  def process_halt_msg(msg):
#      print(f'received answer for halt_msg: {msg.reply_template.answer}')
#      print(f'device is halted')

def bp_addr(offset, code_addr):
    bp_addr = util.sum_hexs([offset, code_addr]) #remove '0x'
    amount_chars = math.floor(len(bp_addr[2:]) / 2)
    if amount_chars % 2 != 0:
        print("WARNING: breakpoint address is not even addr")
        print(f"offset {offset} code_addr {code_addr} chars {amount_chars} calculated addr: {bp_addr}")

    _hex = hex(amount_chars)
    if int(_hex[2:], 16) < 16:
        _hex = '0x0' + _hex[2:]

    print(f'tuple ({_hex}, {bp_addr})')
    return (_hex, bp_addr)
    #  def setDump(self, d, org):
    #      self.__offset = d['start'][0]
    #      self.__originalDump = org
    #      self.__dump = d

    #      #start bytes
    #      int_offs = hex2Int(self.__offset)
    #      d['start']= ['0x0']

    #      #setting pc
    #      d['pc'] = hex(hex2Int(d['pc']) - int_offs)

    #      #settings breakpoints
    #      d['breakpoints'] = [hex(hex2Int(bp) - int_offs) for bp in d['breakpoints']]

    #      #settings functions
    #      for f in d['functions']:
    #          f['from'] = hex(hex2Int(f['from']) - int_offs)
    #          f['to'] = hex(hex2Int(f['to']) - int_offs)

    #      #settings callstack
    #      for cs in d['callstack']:
    #          if (cs['ra'] == '0x0') and (cs['fp'] == -1):
    #              continue
    #          cs['ra'] = hex(hex2Int(cs['ra']) - int_offs)
