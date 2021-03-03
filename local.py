import select
import re
import threading
import signal
import psutil
import os
import socket
import json
import math

from utils import util
#define DUMP_START "DUMP START\n"
#define DUMP_END "DUMP END\n"

#define DUMP_STACK_START "STACK START\n"
#define DUMP_STACK_END "STACK END\n"

#define DUMP_BYTES "BYTES\n"
#define DUMP_BYTES_END "BYTES END\n"

#0000041: 41                                        ; i32.const

DEBUG = True
HOST = 'localhost'
PORT = 3030

RUN = True
WDProcess = None
fp = None
sock = None
sockAtBp = None

OFFSET = "0x55eb29beb020"
DUMP = None
VALS = None
EV_THREAD = None
CURRENT_BP = None

def dbgprint(s):
    if DEBUG:
        print(s)

def errprint(s):
    print(s)
    #TODO exit process

def bp_addr_helper(offset, code_addr):
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

def noisefree(strng):
    return list( filter(lambda s : s != '', strng.split('\n')) )

def recv_size(s):
    dbgprint("receiving")
    b = s.recv(256)
    _str = b.decode()
    dbgprint(f'decode {_str}')
    _split = _str.split('\x00')
    return int(_split[0])


def recv_bytes(s=None):
    s = sock if s is None else s
    _quantity = recv_size(s)
    max_to_read  = 200 #
    dbgprint(f'quantity bytes expected {_quantity}')

    _buff = b''
    while _quantity > 0:
        _read_quantity = _quantity if _quantity < max_to_read else max_to_read
        dbgprint(f'reading {_read_quantity} bytes')
        _buff += s.recv(_read_quantity)
        _quantity -= _read_quantity

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
    dbgprint("send_signal")
    os.kill(WDProcess.info.get('pid'), signal.SIGUSR1)
    return True

def list_pid(inp):
    dbgprint("List pid")
    for p in psutil.process_iter(['pid','name', 'username']):
        dbgprint(p.info)
    return True

def default(inp):
    dbgprint("Default called")
    return False

def pause(_):
    clean_send('03\n')
    send_signal(_)
    byts = recv_bytes()
    process_helper(byts, 'PAUSE!', process_unknown)
    return True

def send_interrupt(inp):
    sts = inp.split(":")
    dbgprint(f"strings {sts}")
    clean_send(sts[1]+ '\n')
    return True

def dump(_):
    global OFFSET

    clean_send('10\n')
    send_signal(_)
    part1 = recv_bytes()
    raw1 = recv_bytes()
    part2 = recv_bytes()
    raw2 = recv_bytes()
    part3 = recv_bytes()
    raw3 = recv_bytes()
    part4 = recv_bytes()
    all_b = [part1, raw1, part2, raw2, part3, raw3, part4]

    for i,b in enumerate(all_b):
        p = 'raw ' if (i + 1) % 2 == 0 else 'part '
        p += str(i + 1)
        dbgprint(f'{p} {i} byts:')
        dbgprint(f'{b}')
        dbgprint("="*25 + '\n')

    json_str = ''

    dump_start = noisefree(part1.decode())
    assert len(dump_start) == 2, 'Expected two elements for dump start'
    assert dump_start[0] == 'DUMP START', "No correct dump start"

    json_str += dump_start[1]

    mem_str = noisefree(part2.decode())
    assert len(mem_str) == 1, 'Expected one element for memory dump'
    assert 'memory' in mem_str[0], "expected memory data"
    json_str += mem_str[0]

    br_tbl_str = noisefree(part3.decode())
    assert len(br_tbl_str) == 1, 'Expected one element for br tbl dump'
    assert 'br_table' in br_tbl_str[0], "expected br_table data"
    json_str += br_tbl_str[0]


    dump_end = noisefree(part4.decode())
    assert len(dump_end) == 2, 'Expected two element dump_end'
    assert 'DUMP END' in dump_end[1], "expected 'DUMP END' as last data"
    json_str += dump_end[0]

    dbgprint("PRIOR parsing json")
    dbgprint(json_str)
    parsed = json.loads(json_str)
    dbgprint("The parsed element")
    dbgprint(parsed)

    tbl = parsed['table']
    tbl['elements'] = raw1

    lm = parsed['memory']
    lm['bytes']=raw2
    brtbl = parsed['br_table']
    brtbl['size'] = int(brtbl['size'], 16)
    brtbl['labels']= raw3

    dbgprint("ALL parsed element")
    dbgprint(parsed)

    old = OFFSET
    OFFSET = parsed['start'][0]
    dbgprint(f'OFFSET from {old} to {OFFSET}')

    return True

def dumpvalues(_):
    clean_send('11\n')
    send_signal(_)

    byts = recv_bytes()

    nf = noisefree(byts.decode())
    assert len(nf) == 3, 'Expected 3 elements for dump values'
    assert nf[0] == 'STACK START'
    assert 'stack' in nf[1]
    assert nf[2] == 'STACK END'
    
    dbgprint("PRIOR parsing json")
    dbgprint(nf[1])
    parsed = json.loads(nf[1])
    dbgprint("The parsed element")
    dbgprint(parsed)

    return True

def process_raw(raw1):
    return raw1

def process_helper(byts, exp_ack, handler, strict=True):
    try:
        _acks = noisefree(byts.decode())
        dbgprint(f'noisefree acks: {_acks}')
        if strict:
            if exp_ack in _acks:
                dbgprint(f'ack: {_acks}')
                _acks.remove(exp_ack)
            else:
                dbgprint(f"expected ack not received: {exp_ack}")
        else:
            i = -1
            for idx,a in enumerate(_acks):
                if exp_ack in a:
                    i = idx
                    break

            if i >=0:
                _pop = _acks.pop(i)
                dbgprint(f'ack: {_pop}')
            else:
                dbgprint(f"expected ack not received: {exp_ack}")

        if len(_acks) > 0:
            handler(byts, _acks)
    except:
        errprint(f'could not decode {byts}')

def run(_):
    clean_send('01\n')
    send_signal(_)
    byts = recv_bytes()
    process_helper(byts, 'Go!', process_unknown)
    return True

def add_bp(inp):
    global EV_THREAD
    #TODO send add bp
    if EV_THREAD is None:
        EV_THREAD =  threading.Thread(target=at_bp_handler,args=())
        EV_THREAD.start()

    split = inp.split(':')
    dbgprint(f"the split {split}")
    (size_hex, addr_hex) = bp_addr_helper(OFFSET, split[1])
    _addbp_interrupt = '06' + size_hex[2:] + addr_hex[2:] + '\n'
    dbgprint(f"ADD BP INTerrupt {_addbp_interrupt}")
    dbgprint(f'OFFSET {OFFSET} BP ADDR {addr_hex}')

    clean_send(_addbp_interrupt.upper())
    send_signal(inp)
    byts = recv_bytes()

    process_helper(byts, 'ADD BP', process_unknown, strict = False)

    return True

def connect(_):
    global sock, sockAtBp

    clean_send('22\n')
    send_signal(_)
    dbgprint(f'connecting to socket at {HOST} port {PORT}')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockAtBp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #  sockAtBp.setblocking(False)
    sock.connect((HOST, PORT))
    sockAtBp.connect((HOST, PORT))

    data = sock.recv(10) #should receive connected!
    dbgprint(f'got as data {data}')
    assert data.decode() == 'connected!'


    timeout_secs = 3
    ready = select.select([sockAtBp], [],[], timeout_secs)
    if ready[0]:
        data2 = sockAtBp.recv(10)
        dbgprint(f'second got as data {data2}')
        assert data2.decode() == 'foratbp!'
    else:
        errprint("event socket failed to connect")

    dump(_)
    run(_)
    return True

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

        dbgprint("at_bp_handler receiving bytes")
        _recv = recv_bytes(sockAtBp).decode()
        dbgprint(f"at_bp_handler: received {_recv}")
        _found = re.search(atbp_rgx, _recv)
        if _found is None:
            dbgprint(f"Reiceved unknown msg {_recv}")
        else:
            dbgprint(f"AT bp! {_recv}")
            CURRENT_BP = _recv
            EV_THREAD = None
            break


def get_handler(inp):
    instructions = ['interrupt', 'send', 'list', 'pause', 'addbp', 'dump', 'run', 'connect', 'values']
    handles = [send_interrupt, send_signal, list_pid, pause, add_bp, dump, run, connect, dumpvalues]

    for idx,i in enumerate(instructions):
        if i in inp:
            return handles[idx]

    return default

if __name__ == "__main__":
    find_process()
    open_tmp_file()
    while RUN:
        inp = input()
        f = get_handler(inp)
        RUN = f(inp)

    fp.close()
