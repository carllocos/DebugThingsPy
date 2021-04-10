import socket
import select
import threading

sock = None
evsock = None
doRead = False
remote = False

def connect(inp = None):
    global sock, evsock
    host = 'localhost'
    port = 8080
    if remote:
        host = "192.168.1.3"  #ESP32 IP in local network
        port = 80

    if inp is None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        evsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        evsock.connect((host, port))
    else:
        _, i = inp.split(":")
        if int(i) == 0:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
        else:
            evsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            evsock.connect((host, port))

def read_sockets(_):
    global sock, evsock, doRead
    while True:
        socks = []
        if sock is not None:
            socks.append(sock)
        if evsock is not None:
            socks.append(evsock)

        if len(socks) == 0:
            continue

        rs, _, _ = select.select(socks, [], [], 0.3)
        for s in rs:
            data = s.recv(1024)
            lendata = len(data)
            which =  f'socket:' if s == sock else f'event:'
            print(f'{which}: #{lendata} {data}')
            print()

def close(inp):
    global sock, evsock
    _, i = inp.split(":")
    print(f"closing {i}")
    if int(i) == 0:
        print("closing 0")
        sock.close()
        sock = None
    else:
        print("closing 1")
        evsock.close()
        evsock = None

def dump(inp):
    global sock
    sock.send(b'10\n')

def default(inp):
    print(f'does not understand {inp}')

def handle(inp):
    instructions = ['connect', 'close', 'dump']
    handles = [connect, close, dump]
    f = None
    for idx,i in enumerate(instructions):
        if i in inp:
            f = handles[idx]
    if f is None:
        f = default
    return f(inp)


if __name__ == "__main__":
    connect()
    si=threading.Thread(target=read_sockets, args=(None,))
    si.start()
    while True:
        handle(input())

    sock.close()
    evsock.close()
