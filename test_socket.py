import inspect

import struct
import select
import re
import threading
import signal
import psutil
import os
import socket
import json
import math
import sys

from utils import util
#define DUMP_START "DUMP START\n"
#define DUMP_END "DUMP END\n"

#define DUMP_STACK_START "STACK START\n"
#define DUMP_STACK_END "STACK END\n"

#define DUMP_BYTES "BYTES\n"
#define DUMP_BYTES_END "BYTES END\n"
dummy_dumpOLD = {'pc': '0x563fcb6f4061', 'start': ['0x563fcb6f4020'], 'breakpoints': ['0x563fcb6f4061', '0x563fcb6f4065'], 'functions': [{'fidx': '0x0', 'from': '0x563fcb6f404c', 'to': '0x563fcb6f404c', 'args': 1, 'locs': 0}, {'fidx': '0x1', 'from': '0x563fcb6f404f', 'to': '0x563fcb6f4064', 'args': 1, 'locs': 0}, {'fidx': '0x2', 'from': '0x563fcb6f4069', 'to': '0x563fcb6f4078', 'args': 0, 'locs': 1}], 'callstack': [{'type': 0, 'fidx': '0x2', 'sp': -1, 'fp': -1, 'block_key': '(nil)', 'ra': '(nil)'}, {'type': 3, 'fidx': '0x0', 'sp': 0, 'fp': 0, 'block_key': '0x563fcb6f406d', 'ra': '0x563fcb6f406f'}, {'type': 0, 'fidx': '0x1', 'sp': 0, 'fp': 0, 'block_key': '(nil)', 'ra': '0x563fcb6f4073'}, {'type': 4, 'fidx': '0x0', 'sp': 2, 'fp': 1, 'block_key': '0x563fcb6f4054', 'ra': '0x563fcb6f4056'}, {'type': 0, 'fidx': '0x1', 'sp': 1, 'fp': 1, 'block_key': '(nil)', 'ra': '0x563fcb6f405d'}, {'type': 4, 'fidx': '0x0', 'sp': 3, 'fp': 2, 'block_key': '0x563fcb6f4054', 'ra': '0x563fcb6f4056'}, {'type': 0, 'fidx': '0x1', 'sp': 2, 'fp': 2, 'block_key': '(nil)', 'ra': '0x563fcb6f405d'}, {'type': 4, 'fidx': '0x0', 'sp': 4, 'fp': 3, 'block_key': '0x563fcb6f4054', 'ra': '0x563fcb6f4056'}, {'type': 0, 'fidx': '0x1', 'sp': 3, 'fp': 3, 'block_key': '(nil)', 'ra': '0x563fcb6f405d'}, {'type': 4, 'fidx': '0x0', 'sp': 5, 'fp': 4, 'block_key': '0x563fcb6f4054', 'ra': '0x563fcb6f4056'}, {'type': 0, 'fidx': '0x1', 'sp': 4, 'fp': 4, 'block_key': '(nil)', 'ra': '0x563fcb6f405d'}, {'type': 4, 'fidx': '0x0', 'sp': 6, 'fp': 5, 'block_key': '0x563fcb6f4054', 'ra': '0x563fcb6f4056'}, {'type': 0, 'fidx': '0x1', 'sp': 5, 'fp': 5, 'block_key': '(nil)', 'ra': '0x563fcb6f405d'}, {'type': 4, 'fidx': '0x0', 'sp': 7, 'fp': 6, 'block_key': '0x563fcb6f4054', 'ra': '0x563fcb6f4056'}], 'globals': [], 'table': {'max': 0, 'elements': []}, 'memory': {'pages': 0, 'total': 0, 'bytes': []}, 'br_table': {'size': '0x100', 'labels': []}}
dummy_valsOLD = {'stack': [{'idx': 0, 'type': 'i32', 'value': 6}, {'idx': 1, 'type': 'i32', 'value': 6}, {'idx': 2, 'type': 'i32', 'value': 5}, {'idx': 3, 'type': 'i32', 'value': 4}, {'idx': 4, 'type': 'i32', 'value': 3}, {'idx': 5, 'type': 'i32', 'value': 2}, {'idx': 6, 'type': 'i32', 'value': 1}]}

dummy_bp = '0x41'
#FIXME table did not send all elements
#FIXME callstack one frame has not same fp the third one
#FIXME the frame have not all same return address
#FIXME stack of values have one extra element
dummy_dump = {'pc': '0x55acdf419092', 'fp': 9, 'start': ['0x55acdf419020'], 'breakpoints': ['0x55acdf419092'], 'functions': [{'fidx': '0x0', 'from': '0x55acdf419074', 'to': '0x55acdf419074', 'args': 1, 'locs': 0}, {'fidx': '0x1', 'from': '0x55acdf419077', 'to': '0x55acdf419077', 'args': 1, 'locs': 0}, {'fidx': '0x2', 'from': '0x55acdf41907a', 'to': '0x55acdf41907a', 'args': 1, 'locs': 0}, {'fidx': '0x3', 'from': '0x55acdf41907d', 'to': '0x55acdf41907d', 'args': 1, 'locs': 0}, {'fidx': '0x4', 'from': '0x55acdf419080', 'to': '0x55acdf419095', 'args': 1, 'locs': 0}, {'fidx': '0x5', 'from': '0x55acdf4190a0', 'to': '0x55acdf4190d6', 'args': 0, 'locs': 4}], 'callstack': [{'type': 0, 'fidx': '0x5', 'sp': -1, 'fp': -1, 'block_key': '(nil)', 'ra': '0x55acdf419069'}, {'type': 3, 'fidx': '0x0', 'sp': 3, 'fp': 0, 'block_key': '0x55acdf4190bb', 'ra': '0x55acdf4190bd'}, {'type': 0, 'fidx': '0x4', 'sp': 7, 'fp': 0, 'block_key': '(nil)', 'ra': '0x55acdf4190c9'}, {'type': 4, 'fidx': '0x0', 'sp': 9, 'fp': 8, 'block_key': '0x55acdf419085', 'ra': '0x55acdf419087'}, {'type': 0, 'fidx': '0x4', 'sp': 8, 'fp': 8, 'block_key': '(nil)', 'ra': '0x55acdf41908e'}, {'type': 4, 'fidx': '0x0', 'sp': 10, 'fp': 9, 'block_key': '0x55acdf419085', 'ra': '0x55acdf419087'}, {'type': 0, 'fidx': '0x4', 'sp': 9, 'fp': 9, 'block_key': '(nil)', 'ra': '0x55acdf41908e'}, {'type': 4, 'fidx': '0x0', 'sp': 11, 'fp': 10, 'block_key': '0x55acdf419085', 'ra': '0x55acdf419087'}, {'type': 0, 'fidx': '0x4', 'sp': 10, 'fp': 10, 'block_key': '(nil)', 'ra': '0x55acdf41908e'}, {'type': 4, 'fidx': '0x0', 'sp': 12, 'fp': 11, 'block_key': '0x55acdf419085', 'ra': '0x55acdf419087'}, {'type': 0, 'fidx': '0x4', 'sp': 11, 'fp': 11, 'block_key': '(nil)', 'ra': '0x55acdf41908e'}, {'type': 4, 'fidx': '0x0', 'sp': 13, 'fp': 12, 'block_key': '0x55acdf419085', 'ra': '0x55acdf419087'}], 'globals': [], 'table': {'max': 5, 'elements': [5, 3, 2, 1, 0]}, 'memory': {'pages': 2, 'total': 32, 'bytes': b' \x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'}, 'br_table': {'size': 256, 'labels': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}}
dummy_vals = {'stack': [{'idx': 0, 'type': 'f32', 'value': 32.3232002}, {'idx': 1, 'type': 'f64', 'value': 64.646464}, {'idx': 2, 'type': 'i32', 'value': 32}, {'idx': 3, 'type': 'i64', 'value': 64}, {'idx': 4, 'type': 'f32', 'value': 32.3232002}, {'idx': 5, 'type': 'f64', 'value': 64.646464}, {'idx': 6, 'type': 'i32', 'value': 32}, {'idx': 7, 'type': 'i64', 'value': 64}, {'idx': 8, 'type': 'i32', 'value': 5}, {'idx': 9, 'type': 'i32', 'value': 4}, {'idx': 10, 'type': 'i32', 'value': 3}, {'idx': 11, 'type': 'i32', 'value': 2}, {'idx': 12, 'type': 'i32', 'value': 1}]}
DEBUG = True
HOST = 'localhost'
PORT = 8080
MAX_BYTES = 100 #FIXME at 20 get issue due to pc_serialization
RECV_INT = '23'
CTR = 0

RUN = True
WDProcess = None
fp = None
sock = None
sockAtBp = None
OFFSET = "0x55cd813d8020"
clientSocket = None
sockets = {}

DUMP = None
VALS = None
EV_THREAD = None
CURRENT_BP = None
KINDS = {'pcState': '01',
         'bpsState': '02',
         'callstackState': '03',
         'globalsState': '04',
         'tblState': '05',
         'memState': '06', 
         'brtblState': '07',
         'stackvalsState': '08'}

WITH_INTERRUPT = False

ONLY = ['dump', 'run', 'add_bp', 'connect', 'debugsession', 'find_process', 'open_tmp_file', 'dumpvalues', 'at_bp_handler']
def dbgprint(s):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    cn =str(calframe[1][3])
    if DEBUG:# and cn in ONLY:
        print((cn + ':').upper(), s)

def errprint(s):
    print(s)
    sys.exit()

def bp_addr_helper(offset, code_addr):
    bp_addr = util.sum_hexs([offset, code_addr]) #remove '0x'
    amount_chars = math.floor(len(bp_addr[2:]) / 2)
    if amount_chars % 2 != 0:
        dbgprint("WARNING: breakpoint address is not even addr")
        dbgprint(f"offset {offset} code_addr {code_addr} chars {amount_chars} calculated addr: {bp_addr}")
    else:
        #  print("okay")
        pass

    _hex = hex(amount_chars)
    if int(_hex[2:], 16) < 16:
        _hex = '0x0' + _hex[2:]

    ##print(f'tuple ({_hex}, {bp_addr})')
    return (_hex, bp_addr)

def noisefree(strng):
    return list( filter(lambda s : s != '', strng.split('\n')) )

def recv_size(s):
    #dbgprint("receiving")
    b = s.recv(4)
    print(f'reciving size 4 bytes {b}')
    s = int.from_bytes(b, 'little')
    print(f'in int {s}')
    return s
    #  _str = b.decode()
    #dbgprint(f'decode {_str}')
    #  _split = _str.split('\x00')
    #  return int(_split[0])
#  def recv_size(s):
#      #dbgprint("receiving")
#      b = s.recv(256)
#      _str = b.decode()
#      #dbgprint(f'decode {_str}')
#      _split = _str.split('\x00')
#      return int(_split[0])


def recv_bytes(s=None):
    s = sock if s is None else s
    _quantity = recv_size(s)
    #  max_to_read  = 200 #
    #dbgprint(f'quantity bytes expected {_quantity}')

    #  _buff = b''
    #  while _quantity > 0:
    #  _read_quantity = _quantity# if _quantity < max_to_read else max_to_read
    #dbgprint(f'reading {_read_quantity} bytes')
    _buff = s.recv(_quantity)
    #  _quantity -= _read_quantity

    return _buff

def clean_send(t):
    fp.seek(0)
    fp.truncate()
    fp.write(t)
    fp.flush()

def find_process(name='WARDuino'):
    global WDProcess
    dbgprint(f"Searching for {name} process")
    for p in psutil.process_iter(['pid','name', 'username']):
        if p.info.get('name') == name:
            WDProcess = p
            dbgprint(f'found process {WDProcess.info}')
            break
    return True

def open_tmp_file(name='change'):
    global fp
    path = '/tmp/'
    fp = open(os.path.join(path, name),'w')
    dbgprint(f'File {name} open at {path}')

def process_unknown(byts, unknown):
    dbgprint(f'received chars unknown msg {unknown}')
    #TODO process at bp


def send_signal(_):
    #dbgprint("send_signal")
    os.kill(WDProcess.info.get('pid'), signal.SIGUSR1)
    return True

def list_pid(inp):
    #dbgprint("List pid")
    for p in psutil.process_iter(['pid','name', 'username']):
        dbgprint(p.info)
    return True

def default(inp):
    dbgprint("Default called")
    return True

def pause(_):
    clean_send('03\n')
    send_signal(_)
    byts = recv_bytes()
    process_helper(byts, 'PAUSE!', process_unknown)
    return True

def send_interrupt(inp):
    sts = inp.split(":")
    #dbgprint(f"strings {sts}")
    clean_send(sts[1]+ '\n')
    return True

def receive_raw_bytes(_bytes, merge = False):
    (_total_elems, _ ) = struct.unpack('<HH', _bytes[0:4])
    _bytes = _bytes[4:] #TODO maybe apply code below only if _total_elems > 0
    (_bytes_per_elemnt, _ ) = struct.unpack('<HH', _bytes[0:4])
    _bytes = _bytes[4:]
    elems = []
    if merge:
        elems = _bytes
    else:
        for i in range(_total_elems):
            off = i * _bytes_per_elemnt
            _b = _bytes[off : off + _bytes_per_elemnt]
            elems.append(_b)
    return elems

def bytes_2_int(b):
    (fix, _) = struct.unpack('<HH', b)
    return fix


def read_from_socket(sock, start, end):
    bufsize = 1024
    wholebuf = b''
    start_found = False
    do_recv = True
    while do_recv:
        _buff = sock.recv(bufsize)
        print(f'read buff of size {len(_buff)}')
        wholebuf += _buff
        d = _buff.decode()
        if not start_found:
            if d.find(start) >=0:
                start_found = True
            else:
                assert False, f"start not found in {d}"
        else:
            if d.find(end) >= 0:
                do_recv = False

    return wholebuf

#  def read_from_socket(sock, start, end):
#      _wholebuf = b''
#      first_passed = False
#      doRead = True
#      while doRead:
#          bufsize = sock.recv(4)
#          print(f'reciving size 4 bytes {bufsize} len={len(bufsize)}')
#          _quantity = int.from_bytes(bufsize, 'little')
#          print(f'in int {_quantity}')
#          _buff = sock.recv(_quantity)
#          if len(_buff) < _quantity:
#              assert False, f'expected size {_quantity} got {len(_buff)}'

#          if first_passed:
#              d = _buff.decode()
#              if end in d:
#                  doRead = False
#          else:
#              first_passed = True
#              d = _buff.decode()
#              if start in d:
#                  print("passed first!")
#              else:
#                  assert False, f"not passed first {start} in {d}"

#          _wholebuf += _buff
#          if end == _buff:
#              break

#      return _wholebuf

def dump(_):
    global sockets, clientSocket
    #  global OFFSET, DUMP, dummy_dump, DEBUG, CTR

    sock = sockets[clientSocket]
    if safe_send(sock, '10\n'.encode()) < 0:
        print("error sending dump")

    #FIXME be careful some frames have as return address nil!!

    #  clean_send('10\n')
    #  send_signal(_)
    #  return True
    #  DEBUG = False if CTR < 1 else True
    #  CTR += 1

    #  buf = read_from_socket(sock, "DUMP!\n", "\n")
    #  #  part1 = recv_bytes(sock)
    #  print(f'read PART1 {buf}')
    return True

    #  raw1 = recv_bytes()
    #  part2 = recv_bytes()
    #  raw2 = recv_bytes()
    #  part3 = recv_bytes()
    #  raw3 = recv_bytes()
    #  part4 = recv_bytes()
    #  all_b = [part1, raw1, part2, raw2, part3, raw3, part4]

    #  for i,b in enumerate(all_b):
    #      p = 'raw ' if (i + 1) % 2 == 0 else 'part '
    #      p += str(i + 1)
    #      #  #dbgprint(f'{p} {i} byts:')
    #      #  #dbgprint(f'{b}')
    #      #  #dbgprint("="*25 + '\n')

    #  json_str = ''

    #  dump_start = noisefree(part1.decode())
    #  assert len(dump_start) == 2, 'Expected two elements for dump start'
    #  assert dump_start[0] == 'DUMP START', "No correct dump start"

    #  json_str += dump_start[1]

    #  mem_str = noisefree(part2.decode())
    #  assert len(mem_str) == 1, 'Expected one element for memory dump'
    #  assert 'memory' in mem_str[0], "expected memory data"
    #  json_str += mem_str[0]

    #  br_tbl_str = noisefree(part3.decode())
    #  assert len(br_tbl_str) == 1, 'Expected one element for br tbl dump'
    #  assert 'br_table' in br_tbl_str[0], "expected br_table data"
    #  json_str += br_tbl_str[0]


    #  dump_end = noisefree(part4.decode())
    #  assert len(dump_end) == 2, 'Expected two element dump_end'
    #  assert 'DUMP END' in dump_end[1], "expected 'DUMP END' as last data"
    #  json_str += dump_end[0]

    #  #  #dbgprint("PRIOR parsing json")
    #  #  #dbgprint(json_str)
    #  parsed = json.loads(json_str)
    #  #  dbgprint("The parsed element")
    #  #  dbgprint(parsed)

    #  tbl = parsed['table']
    #  tbl['elements'] = list(map(bytes_2_int, receive_raw_bytes(raw1)))

    #  lm = parsed['memory']
    #  lm['bytes']=raw2
    #  brtbl = parsed['br_table']
    #  brtbl['size'] = int(brtbl['size'], 16)
    #  brtbl['labels']= list(map(bytes_2_int, receive_raw_bytes(raw3)))

    #  dbgprint("dump")
    #  dbgprint(parsed)

    #  old = OFFSET
    #  OFFSET = parsed['start'][0]
    #  dbgprint(f'OFFSET from {old} to {OFFSET}')
    #  dummy_dump['start'] = [OFFSET]
    #  DUMP = parsed
    #  return True

def dumpvalues(_):
    global VALS, clientSocket, sockets
    sock = sockets[clientSocket]
    if safe_send(sock, '11\n'.encode()) < 0:
        print("error sending dump")

    return True
    #  clean_send('11\n')
    #  send_signal(_)

    #  byts = recv_bytes()

    #  nf = noisefree(byts.decode())
    #  assert len(nf) == 3, 'Expected 3 elements for dump values'
    #  assert nf[0] == 'STACK START'
    #  assert 'stack' in nf[1]
    #  assert nf[2] == 'STACK END'
    
    #  #  #dbgprint("PRIOR parsing json")
    #  #  #dbgprint(nf[1])
    #  parsed = json.loads(nf[1])
    #  dbgprint("The Values")
    #  dbgprint(parsed)

    #  VALS = parsed
    #  return True

def process_raw(raw1):
    return raw1

def process_helper(byts, exp_ack, handler, strict=True):
    try:
        _acks = noisefree(byts.decode())
        dbgprint(f'noisefree acks: {_acks}')
        if strict:
            if exp_ack in _acks:
                #dbgprint(f'ack: {_acks}')
                _acks.remove(exp_ack)
            else:
                dbgprint(f"expected ack `{exp_ack}` not received")
        else:
            i = -1
            for idx,a in enumerate(_acks):
                if exp_ack in a:
                    i = idx
                    break

            if i >=0:
                _pop = _acks.pop(i)
                #dbgprint(f'ack: {_pop}')
            else:
                dbgprint(f"expected ack not received: {exp_ack}")

        if len(_acks) > 0:
            handler(byts, _acks)
    except:
        errprint(f'could not decode {byts}')

def run(_):
    clean_send('01\n')
    send_signal(_)
    #  byts = recv_bytes()
    #  process_helper(byts, 'Go!', process_unknown)
    return True

def add_bp(inp):
    global EV_THREAD, DEBUG, sockets
    #TODO send add bp
    DEBUG = True

    split = inp.split(':')
    print(f"using OFFSET {split[2]}")
    #  #dbgprint(f"the split {split}")
    (size_hex, addr_hex) = bp_addr_helper(split[2], split[1])
    _addbp_interrupt = '06' + size_hex[2:] + addr_hex[2:] + '\n'
    sock = sockets['io']
    if sock.send(_addbp_interrupt.upper().encode()) < 0:
        print('issue occured while sending ad bp')

    #dbgprint(f"ADD BP Interrupt {_addbp_interrupt}")
    #  #dbgprint(f'OFFSET {OFFSET} BP ADDR {addr_hex}')


    #  clean_send(_addbp_interrupt.upper())
    #  send_signal(inp)
    #  byts = recv_bytes()

    #  process_helper(byts, 'ADD BP', process_unknown, strict = False)

    return True




def close(_):
    global clientSocket
    sock = sockets[clientSocket]
    sock.close()

def safe_send(sock, content):
    global WITH_INTERRUPT

    i = sock.send(content)
    #  if WITH_INTERRUPT:
    #      send_signal('du')

    return i


def send_the_signal(a):
    import time
    while True:
        time.sleep(400/1000)
        send_signal("dum")

def connect(inputs):
    global sockets, PORT, HOST, clientSocket, WITH_INTERRUPT
    #  inputs = "connect:all:0x01"

    vals = inputs.split(":")
    name =None
    flags = None
    if len(vals) == 3:
        name = vals[1]
        flags = vals[2]
    else:
        flags = vals[1]

    b = int(flags, 16).to_bytes(1, 'big')

    if name is None:
        if int(flags, 16) == 3:
            name = 'io'
        elif int(flags, 16)  == 8:
            name = 'dbg'
        elif int(flags, 16) == 16:
            name ='event'
        else:
            name = str(int(flags, 16))

    print(f'connecting to PORT {PORT} socket `{name}` with flags `{flags}`')
    if WITH_INTERRUPT:
        si=threading.Thread(target=send_the_signal, args=(2,))
        si.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    
    print(f'sending socket config {b}')
    safe_send(sock, b)

    r = sock.recv(1) #echo the config
    assert r == b, "not equal config"
    print(f'received concifg {r}')
    intf = int(flags, 16)
    if intf == 3 or intf == 1:
        r = sock.recv(4)
        print(f'maximum recv buf size for device {r}')

    if  intf == 3:
        evt = threading.Thread(target=start_recv, args=(sock,))
        evt.start()

    if intf == 8:
        start_recv(sock)

    sockets[name] = sock
    clientSocket = name
    #  print(f'total sockets now #{len(sockets)}')
    print(f'new socket fd={sockets[name].fileno()} `{name}`= {sockets[name]} ')
    return True

def start_recv(sock):
    print("START receive Debug info")
    timeout_secs = 1
    _buff = b''
    while True:
        ready = select.select([sock], [],[], timeout_secs)
        #  send_signal("send")
        if not ready[0]:
            continue

        _buff += sock.recv(1024)
        try:
            d = _buff.decode()
            print(_buff.decode(), end="")
            _buff = b''
        except:
            print( "failed to decode")


def send_socket(inputs):
    global sockets, clientSocket
    vals = inputs.split(':')
    name = clientSocket
    content = vals[1]

    if len(vals) == 3 :
        name = vals[1]
        content = vals[2]

    sock = sockets.get(name, None)
    if sock is None:
        print(f"no such socket `{name}`")
        return True
    print(f'sending to socket `{name}` fd={sock.fileno()}#{len(content)} bytes content `{content}`')

    i = safe_send(sock, content.encode())

    print(f"done sending #{i} bytes")
    return True

#  def connect(inp):
#      global sock, sockAtBp, PORT
#      if ':' in inp:
#          PORT = int(inp.split(':')[1])
#          port_hex = signedint2bytes(PORT, 4).hex()
#          clean_send('22' + port_hex + '\n')
#      else:
#          clean_send('22\n')

#      send_signal('notimp')
#      dbgprint(f'connecting to socket at {HOST} port {PORT}')
#      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#      sockAtBp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#      #  sockAtBp.setblocking(False)
#      sock.connect((HOST, PORT))
#      sockAtBp.connect((HOST, PORT))

#      data = sock.recv(10) #should receive connected!
#      dbgprint(f'socket received {data}')
#      assert data.decode() == 'connected!'


#      timeout_secs = 3
#      ready = select.select([sockAtBp], [],[], timeout_secs)
#      if ready[0]:
#          data2 = sockAtBp.recv(10)
#          dbgprint(f'socket received {data2}')
#          assert data2.decode() == 'foratbp!'
#      else:
#          errprint("event socket failed to connect")

#      dump('notimp')
#      run('notimp')
#      return True

def at_bp_handler():
    global sockAtBp, CURRENT_BP, EV_THREAD
    dbgprint("AT BP Handler")
    timeout_secs = 1
    ctr = 0
    atbp_rgx = "^AT \w\w*!\n$" #"AT %p!\n"

    while True:
        ready = select.select([sockAtBp], [],[], timeout_secs)
        if not ready[0]:
            dbgprint("NOT READY")
            continue

        #  #dbgprint("at_bp_handler receiving bytes")
        _recv = recv_bytes(sockAtBp).decode()
        #dbgprint(f"at_bp_handler: received {_recv}")
        _found = re.search(atbp_rgx, _recv)
        if _found is None:
            dbgprint(f"Reiceved unknown msg {_recv}")
        else:
            dbgprint(f"AT bp! {_recv}")
            CURRENT_BP = _recv
            EV_THREAD = None
            break

def debugsession(_):
    global DUMP, VALS, CURRENT_BP

    dump(_)
    dumpvalues(_)
    display(_)
    return True

def display(_):
    c = clean_session(DUMP, VALS, None)
    print(c)
    print("="*12)
    return True

def signedint2bytes(i, quantity, byteorder='big'):
    return (i).to_bytes(quantity, byteorder, signed = True)

def int2bytes(i, quantity, byteorder = 'big'):
    return (i).to_bytes(quantity, byteorder) #'little'

def float2bytes(val, quantity, byteorder = 'big'):

    if quantity not in [4, 8]:
        raise ValueError(f'requested incorrect quantity of bytes {quantity}')

    #get 4 byte single precision with struct
    #'>' big endian
    fmt = 'f' if quantity == 4 else 'd'
    fmt = ('>' if byteorder == 'big' else '<') + fmt

    #  #dbgprint(f"formating value with {fmt}")
    b = struct.pack(fmt, val) 
    #  #dbgprint(f'value {val} becomes {b}')
    return b

def make_evenaddr(addr):
    noXo = addr[2:]
    chars_missing = len(noXo) %2
    if chars_missing == 0:
        return noXo
    else:
        return "0" * chars_missing + noXo

def serialize_pointer(addr):
    #dbgprint(f'serialize addr {addr} no offset {addr[2:]}')
    with_pad = make_evenaddr(addr)
    #dbgprint(f'new addr 0x{with_pad}')
    size = int2bytes(len(with_pad) // 2, 1)
    #dbgprint(f'size pointer {size} in hex {size.hex()} and addr {with_pad}')
    return (size.hex()+ with_pad, size)

def add_in_chunks(chunks, serialization, max_space):
    if len(chunks) > 0:
        last = chunks[-1]
        if len(last) + len(serialization) <= max_space:
            chunks[-1] = last + serialization
        else:
            chunks.append(serialization)
    else:
        chunks.append(serialization)

def serialie_pc(pc_addr, chunks, max_space):
    #TODO add padding to the pointer to make even chars
    #dbgprint(f"serialie_pc: {pc_addr}")
    kind = KINDS['pcState']
    (p, _) = serialize_pointer(pc_addr)
    pc_ser = kind + p 
    #dbgprint(f"pc_ser - {kind} {p}")
    add_in_chunks(chunks, pc_ser, max_space)
    #dbgprint(f'TOTAL CHunks {len(chunks)}')

def serialize_breakpoints(bps, chunks, max_space):
    #dbgprint(f'serializing bps {bps}')
    kind = KINDS['bpsState']
    header_len = len(kind) + 2# 2 chars needed to express quantity of breakpoints
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    bps_ser = ""
    quantity_bps = 0

    def add_chunk():
        nonlocal kind, quantity_bps, bps_ser, current_chunk
        header = kind + int2bytes(quantity_bps, 1).hex()
        #dbgprint(f'making chunk for #{quantity_bps} bps')
        #dbgprint(f'header {header} - {bps_ser}')
        #dbgprint(f'current_chunk {current_chunk}')
        chunks.append(current_chunk + header + bps_ser)

    for bp in bps:
        (_serbp, _) = serialize_pointer(bp)
        if max_space <  len(current_chunk) + header_len + len(bps_ser) + len(_serbp):
            #dbgprint(f'call whitin for add_chunk: bp not added yet {bp} with ser {_serbp}')
            if bps_ser != '':
                add_chunk()
            else:
                #dbgprint("in the else")
                chunks.append(current_chunk)
            quantity_bps = 0
            bps_ser = ""
            current_chunk = ""

        quantity_bps += 1
        bps_ser += _serbp

    if bps_ser != "":
        #dbgprint("breakpoints_ser: call from outsite for")
        add_chunk()
    elif current_chunk != "":
        chunks.append(current_chunk)
    #dbgprint(f'TOTAL CHunks {len(chunks)}')

def val2bytes(value_type, val):
    qb = 4 if value_type[1:] == '32' else 8
    if value_type[0] == 'i':
        #  #dbgprint(f'serializing {value_type}')
        return int2bytes(val, qb, byteorder='little')
    else:
        #float case
        return float2bytes(val, qb, byteorder='little')

def serialize_stackvalues(vals, chunks, max_space):
    #dbgprint(f'#{len(vals)} Stack Values to serialize MAX_space {max_space}')
    kind = KINDS['stackvalsState']
    header_len = len(kind) + 4# 4 chars for quantity stack values
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    quantity_sv = 0
    vals_ser = ""
    dbgprint(f"chunck used #{len(current_chunk)}")
    def add_chunk():
        nonlocal kind, quantity_sv, vals_ser, current_chunk
        dbgprint(f'making chunk for #{quantity_sv} values')
        header = kind + int2bytes(quantity_sv, 2).hex()
        chunks.append(current_chunk + header + vals_ser)
        dbgprint(f'chunk idx {len(chunks) -1} chunk {len(chunks[-1])}')
        assert len(chunks[-1]) <= max_space, f'failed for chunk idx {len(chunks) -1 } #{len(chunks[-1])}'

    for vobj in vals:
        t = int2bytes(valtype2int(vobj['type']), 1).hex()
        v =  val2bytes(vobj['type'], vobj['value']).hex()
        _serval = t + v
        if max_space < len(current_chunk) + header_len + len(vals_ser) + len(_serval) :
            if vals_ser != '':
                add_chunk()
            else:
                dbgprint("in the else")
                chunks.append(current_chunk)
            quantity_sv = 0
            vals_ser = ""
            current_chunk = ""
        
        quantity_sv +=1
        vals_ser += _serval
    
    if vals_ser != "":
        add_chunk()
    elif current_chunk != "":
        dbgprint("in the elif")
        chunks.append(current_chunk)

def isfunc_type(frame):
    return frame['type'] == 0
#  DD_CHUNK: chunk for #1 frames
#  ADD_CHUNK: chunk for #2 frames
#  ADD_CHUNK: chunk for #2 frames
#  ADD_CHUNK: chunk for #2 frames
#  ADD_CHUNK: chunk for #2 frames
#  ADD_CHUNK: chunk for #2 frames
#  ADD_CHUNK: chunk for #1 frames

def serialize_callstack(callstack, chunks, max_space):
    dbgprint(f'serialzing #{len(callstack)} frames with max_space {max_space}')

    kind = KINDS['callstackState']
    header_len = len(kind) + 4# 4 chars for quantity stack values
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    quantity = 0
    frames_ser = ""
    #dbgprint(f"chunck used #{len(current_chunk)}")
    dbgframes = []

    def add_chunk():
        nonlocal kind, quantity, frames_ser, current_chunk
        quantity_ser = int2bytes(quantity, 2).hex()
        header = kind + quantity_ser
        dbgprint(f"chunk for #{quantity} frames")
        chunks.append(header + frames_ser)
        for i,f in enumerate(dbgframes):
            dbgprint(f'i:{i} frame {f}')

    for frame in callstack:

        type_ser = int2bytes(frame['type'], 1).hex()
        sp_ser = signedint2bytes(frame['sp'], 4).hex()
        fp_ser = signedint2bytes(frame['fp'], 4).hex()
        (retaddr_ser, _) = serialize_pointer(frame['ra'])
        frame_ser = type_ser + sp_ser + fp_ser + retaddr_ser
        if isfunc_type(frame):
            fid = int(frame['fidx'], 16)
            funcid_ser = int2bytes( fid, 4).hex()
            frame_ser += funcid_ser
        else:
            (blockaddr_ser, _) = serialize_pointer(frame['block_key'])
            frame_ser += blockaddr_ser

        #dbgprint(f'frame {frame} - {frame_ser}')
        if max_space < len(current_chunk) + header_len + len(frames_ser) + len(frame_ser) :
            if frames_ser != '':
                add_chunk()
            else:
                #dbgprint("in the else")
                chunks.append(current_chunk)
            quantity = 0
            frames_ser = ""
            current_chunk = ""
            dbgframes = []

        dbgframes.append(frame)
        quantity +=1
        frames_ser += frame_ser
    
    if frames_ser != "":
        add_chunk()
    elif current_chunk != "":
        chunks.append(current_chunk)


def serialize_table(tbl, chunks, max_space):
    #dbgprint(f"serializing  #{len(tbl['elements'])} elements with {tbl}")
    kind = KINDS['tblState']
    funref = 17
    elem_type_bytes = 1 #1 byte to hold which kind of elements hold in table. Although for now only funcrefs
    elems_quantity_bytes = 4 #quantity bytes used to express quantity of elements
    header_len = len(kind) + (elem_type_bytes + elems_quantity_bytes) * 2 

    #dbgprint(f'header len {header_len}')
    quantity = 0
    elems_ser = ""
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    #dbgprint(f'current_chunk #{len(current_chunk)}')

    def add_chunk():
        nonlocal kind, quantity, elems_ser, current_chunk, elem_type_bytes, elems_quantity_bytes, funref
        quanty_hex = int2bytes(quantity, elems_quantity_bytes, byteorder='big').hex()
        elems_type_hex = int2bytes(funref, elem_type_bytes, byteorder='big').hex()
        header = kind + elems_type_hex + quanty_hex
        chunks.append(current_chunk + header + elems_ser)
        #dbgprint(f'chunk idx {len(chunks) -1} chunk {len(chunks[-1])}')
        assert len(chunks[-1]) <= max_space, f'failed for chunk idx {len(chunks) -1 } #{len(chunks[-1])}'

    for e in tbl['elements']:
        e_ser = int2bytes(e, 4, byteorder='big').hex()
        #dbgprint(f'{max_space} < {len(current_chunk)} + {header_len}+ {len(elems_ser)} + {len(e_ser)}')
        if max_space < len(current_chunk) + header_len + len(elems_ser) + len(e_ser):
            if elems_ser != '':
                add_chunk()
            else:
                #dbgprint("in the else")
                chunks.append(current_chunk)
            quantity = 0
            elems_ser = ""
            current_chunk = ""
        
        quantity +=1
        elems_ser += e_ser

    if elems_ser != "":
        add_chunk()
    elif current_chunk != "":
        chunks.append(current_chunk)
    #dbgprint(f'total chunks {len(chunks)}')


def serialize_first_msg(session):
    #globals
    gls = session['globals']
    kind_globals = KINDS['globalsState']
    #  quantity_globals = int2bytes(len(gls), 4).hex()
    quantity_globals = int2bytes(50, 4).hex()
    gls_ser = ''
    for g in gls:
        pass

    globals_ser = kind_globals + quantity_globals + gls_ser

    #Table
    tbl = session['table']
    kind_table = KINDS['tblState'] 
    #dbgprint("tbl is missing init") #FIXME init
    _init = tbl.get('init', None)
    if _init is None:
        #dbgprint("tbl init is 0")
        _init = 0
    init_ser = int2bytes(_init, 4).hex()

    _max = tbl.get('max', None)
    if _max is None:
        #dbgprint("tbl max is 0")
        _max = 0

    max_ser = int2bytes(_max, 4).hex()
    tbl_size = int2bytes(len(tbl['elements']), 4).hex();
    tbl_ser = kind_table + init_ser + max_ser + tbl_size

   # memory
    mem = session['memory']
    kind_mem = KINDS['memState']
    tot_ser = int2bytes(12, 4).hex()
    #  tot_ser = int2bytes(mem['total'], 4).hex()
    #dbgprint("memory init is missing AND is prorety max or total?") #FIXME init
    minit_ser = int2bytes(222, 4).hex()
    #  minit_ser = int2bytes(0, 4).hex()
    currentp_ser = int2bytes(mem['pages'], 4).hex()
    mem_ser = kind_mem + tot_ser + minit_ser + currentp_ser
    #dbgprint(f'globals {globals_ser} - table {tbl_ser} - mem {mem_ser}')
    return globals_ser + tbl_ser + mem_ser

def size_and_assert(ser):
    l = len(ser)
    assert l % 2 == 0, f'no even size for serialialization {ser}'

    return l // 2

#TODO always free_space - len(QUANTITY_HEXA CHARS)
# if max size is x that means I can send maximum x bytes so x chars because each char is 1 byte. 
# warduino merges 2 bytes into one byte
def serialize_session(d, v):
    dump = dummy_dump if d is None else d
    vals = dummy_vals if v is None else v

    cleaned = clean_session(dump, vals, None)
    recv_int = RECV_INT

    quanty_bytes_header = 1 + 4 #1 byte for interrupt (= 2 hexa chars) & 4 bytes for quantity bytes send (= 8 hexa chars)
    quanty_last_bytes = 2 #2 bytes, one to tell whether end or not and one for newline
    bytes_lost = quanty_bytes_header + quanty_last_bytes
    max_space = MAX_BYTES - (bytes_lost * 2)
    #first recieve interrupt
    first_msg  = serialize_first_msg(cleaned)

    chunks = [] 

    serialie_pc(cleaned['pc'], chunks, max_space)
    serialize_breakpoints(cleaned['breakpoints'], chunks, max_space)
    serialize_stackvalues(cleaned['stack'], chunks, max_space)
    serialize_table(cleaned['table'], chunks, max_space)
    serialize_callstack(cleaned['callstack'], chunks, max_space)

    chunks.insert(0, first_msg)
    last = len(chunks) - 1
    ds_chunks = []
    for i, c in enumerate(chunks):
        done = '01' if i == last else '00'
        size = size_and_assert(c + done)
        size_ser = int2bytes(size, 4).hex()
        ds_chunks.append( recv_int + size_ser +  c + done)

    #dbgprint("Done serialization")
    #dbgprint(f"{ds_chunks}")

    for i,c in enumerate(ds_chunks):
        assert len(c) <= MAX_BYTES, f'chunk {i} of len {len(c)}'
        assert len(c) % 2 == 0, f'Not an even chars chunk {c}'
    return [c.upper() for c in ds_chunks]

def serialize_test(_):
    serialize_session(DUMP, VALS)
    return True

def rebase_addr(point, offset, new_offset):
    addr = util.substract_hexs([point, offset])
    raddr = hex(int(addr, 16) + int(new_offset, 16))
    return raddr

def clean_session(dump, vals, new_offset):
    offset = dump['start'][0]
    new_offset = offset if new_offset is None else new_offset #TODO remove
    pc = rebase_addr(dump['pc'], offset, new_offset)

    #dbgprint("CAREFull: PC is actually **pc")
    if len(pc[2:]) > 2:
        #  errprint(f"PC {pc} is composed of more than 2 hexachars thus cannot be converted to uint8_t")
        dbgprint(f"PC {pc} is composed of more than 2 hexachars thus cannot be converted to uint8_t")

    bps = [rebase_addr(p, offset, new_offset) for p in dump['breakpoints']]
    for b in bps:
        if len(b[2:]) > 2:
            #  errprint(f"breakpoint {b} is composed of more than 2 hexachars cannot be converted to uint8_t")
            dbgprint(f"breakpoint {b} is composed of more than 2 hexachars cannot be converted to uint8_t")

    callstack = []
    for frame in dump['callstack']:
        _f = {
            'type': frame['type'],
            'fidx': frame['fidx'],
            'sp': frame['sp'],
            'fp': frame['fp'],
        }

        ra = frame['ra']
        bk = frame['block_key']
        _f['ra'] = "" if 'nil' in ra else rebase_addr(frame['ra'], offset, new_offset)
        _f['block_key'] = "" if 'nil' in bk else rebase_addr(frame['block_key'], offset, new_offset)
        callstack.append(_f)
        if _f['ra'] == '':
            dbgprint(f'WARNING ---- frame ra=`` prev ra={frame["ra"]}  rebase_addr={rebase_addr(frame["ra"], offset, new_offset)}')

    br_table = ""
    tb = dump['table']
    gs = dump['globals']
    mem = dump['memory']
    stack = []
    for s in vals['stack']:
        stack.append({
                'type': s['type'],
                #  'type': valtype2int(s['type']),
                'value': s['value']
            })

    cleaned = {'pc': pc,
               'breakpoints': bps,
               'callstack': callstack,
               'globals': gs,
               'table': tb,
               'br_table': br_table,
               'memory': mem,
               'stack': stack }
    return cleaned

def str2hex(s):
    return s.hex()

def json2hex(j):
    s = json.dumps(j)
    return str2hex(s)


def valtype2int(t):
    if t == 'i32':
        return 0
    elif t == 'i64':
        return 1
    elif t == 'f32':
        return 2

    elif t == 'f64':
        return 3
    else:
        errprint(f"Unknwon stack value type {t}")

def sendstate(_):
    global DUMP, VALS

    if DUMP is None:#  or VALS is None:
        errprint('DUMP or VALS not loaded')

    dhex = json2hex(DUMP)
    #  vhex = json2hex(VALS)
    #dbgprint(f"DUMP hex {dhex}")
    #  #dbgprint(f"VALS hex {vhex}")

    return False

def uploadDebugsession(_):
    sers = serialize_session(None, None)
    l = len(sers)
    for i, s in enumerate(sers):
        dbgprint(f'{i}/{l - 1} sending {s}')
        if WDProcess is None:
            continue
        clean_send(s +'\n')
        send_signal(_)
        #dbgprint(f'idx: {i} waiting for ack')
        b = recv_bytes()
        ack = 'done!' if (i + 1) == l else 'ack!'
        process_helper(b, ack, process_unknown)
    return True


def dbg(inp):
    offset = "ERRORERROR"
    code_addr = "ERRORORORORO"
    inputs = inp.split(':')
    bp_addr = inputs[1]
    amount_chars = math.floor(len(bp_addr[2:]) / 2)
    if amount_chars % 2 != 0:
        dbgprint("WARNING: breakpoint address is not even addr")
        dbgprint(f"offset {offset} code_addr {code_addr} chars {amount_chars} calculated addr: {bp_addr}")
    else:
        #  print("okay")
        pass

    _hex = hex(amount_chars)
    if int(_hex[2:], 16) < 16:
        _hex = '0x0' + _hex[2:]

    ##print(f'tuple ({_hex}, {bp_addr})')
    hex_code = '07' if len(inputs) == 3 else '06'
    if hex_code == '07':
        print("removing bp")
    else:
        print("addingbp")
    _addbp_interrupt = hex_code + _hex[2:] + bp_addr[2:] + '\n'
    #dbgprint(f"ADD BP Interrupt {_addbp_interrupt}")
    #  #dbgprint(f'OFFSET {OFFSET} BP ADDR {addr_hex}')

    clean_send(_addbp_interrupt.upper())
    send_signal(inp)
    return True

def get_handler(inp):
    #  instructions = ['dbg', 'interrupt', 'send', 'list', 'pause', 'addbp', 'dump', 'run', 'connect', 'values', 'state', 'display', 'debugsession', 'upload', 'serialize']
    #  handles = [dbg, send_interrupt, send_signal, list_pid, pause, add_bp, dump, run, connect, dumpvalues, sendstate, display, debugsession, uploadDebugsession, serialize_test]

    instructions = ['connect', 'send','add_bp', 'dump', 'close', 'local']
    handles = [connect, send_socket, add_bp, dump, close, dumpvalues]
    for idx,i in enumerate(instructions):
        if i in inp:
            return handles[idx]

    return default

if __name__ == "__main__":
    if WITH_INTERRUPT:
        find_process()
    #  open_tmp_file()
    while RUN:
        inp = input()
        f = get_handler(inp)
        RUN = f(inp)

    #  fp.close()
