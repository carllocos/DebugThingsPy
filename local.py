import signal
import psutil
import os
import socket


DEBUG = True
HOST = 'localhost'
PORT = 3030

RUN = True
WDProcess = None
fp = None
sock = None

def dbgprint(s):
    if DEBUG:
        print(s)
def errprint(s):
    print(s)
    #TODO exit process

def noisefree(strng):
    return list( filter(lambda s : s != '', strng.split('\n')) )

def recv_size():
    dbgprint("receiving")
    b = sock.recv(256)
    _str = b.decode()
    dbgprint(f'decode {_str}')
    _split = _str.split('\x00')
    return int(_split[0])


def recv_bytes():
    _quantity = recv_size()
    max_to_read  = 20 #
    dbgprint(f'quantity bytes expected {_quantity}')

    _buff = b''
    while _quantity > 0:
        _read_quantity = _quantity if _quantity < max_to_read else max_to_read
        dbgprint(f'reading {_read_quantity} bytes')
        _buff += sock.recv(_read_quantity)
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
    clean_send('10\n')
    send_signal(_)
    return True

def process_helper(byts, exp_ack, handler):
    try:
        _acks = noisefree(byts.decode())
        dbgprint(f'noisefree acks: {_acks}')
        if exp_ack in _acks:
            dbgprint(f'ack: {_acks}')
            _acks.remove(exp_ack)
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
    pass

def connect(_):
    global sock
    clean_send('22\n')
    send_signal(_)
    dbgprint(f'connecting to socket at {HOST} port {PORT}')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    data = sock.recv(10)
    dbgprint(f'got as data {data}')
    return True

def get_handler(inp):
    instructions = ['interrupt', 'send', 'list', 'pause', 'add', 'dump', 'run', 'connect']
    handles = [send_interrupt, send_signal, list_pid, pause, add_bp, dump, run, connect]

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
