"""
Measure the debug session sizes of WARDuino for the first five steps
"""

import json
from os import read
from serial.serialposix import Serial
import math

import serial
import serial.tools.list_ports
import time
import sys

def sum_hexs(hexs):
    sum = 0
    for h in hexs:
       x = h if isinstance(h, int) else int( h[2:], 16)
       sum += x

    return hex(sum)

def bp_addr_helper(offset, code_addr):
    bp_addr = sum_hexs([offset, code_addr])  # remove '0x'
    amount_chars = math.floor(len(bp_addr[2:]) / 2)
    if amount_chars % 2 != 0:
        print("WARNING: breakpoint address is not even addr")
        print(
            f"offset {offset} code_addr {code_addr} chars {amount_chars} calculated addr: {bp_addr}")
    else:
        pass

    _hex = hex(amount_chars)
    if int(_hex[2:], 16) < 16:
        _hex = '0x0' + _hex[2:]
    content = '06' + _hex[2:] + bp_addr[2:] + '\n'
    return content.upper()

def await_output(s: serial.Serial, target: str, display = True):
    target = target.encode('utf-8')
    content = b''
    while True:
        b = s.read()
        if display:
            print(f'Content: {content}')
        if b == b'\r':
            continue

        content += b
        pos = content.find(target)
        if pos != -1:
            if display:
                print(f"noise {content[0:pos]}") 
            return content[pos:]

def read_until(s: serial.Serial, target: str, display = True):
    target = target.encode('utf-8')
    target_len = len(target)
    content = b''
    while True:
        b = s.read()
        if display:
            print(f'Content: {content}')
        if b == b'\r':
            continue

        content += b
        content_len = len(content)
        if len(content) >= target_len:
            suffix = content[content_len - target_len : ]
            if  suffix == target:
                return content

def read_all(s: serial.Serial):
    print("READING ALL")
    content = b''
    while True:
        print("in while")
        b = s.read()
        if b == b'\r':
            continue

        content += b
        print(content)

def ask_debug_session(serial: serial.Serial, callstack_size : int):
    #ask dump
    print('asking for dump')
    serial.write('10\n'.encode())

    await_output(serial, 'DUMP!\n', display = False)
    raw_dump  = read_until(serial, "]}\n", display = False)[0:-1]

    dump = raw_dump.decode()
    ddump = json.loads(dump)
    l = len(ddump['callstack'])
    assert  l <= callstack_size, f'callstack size {callstack_size} > {l}'

    #ask locals
    print('asking for locals')
    serial.write('11\n'.encode())
    await_output(serial, "DUMP LOCALS!\n\n", display = False)
    raw_locals = read_until(serial, "}\n\n", display = False)[0:-2]
    locs = raw_locals.decode()
    assert 'count' in locs, f'got {locs}'

    return raw_dump, raw_locals


if __name__ == "__main__":
    port = None
    ports = [port.device for port in serial.tools.list_ports.comports()]
    if not ports:
        print("Device not found!")
        exit(1)
    elif len(ports) > 1:
        print("More than one serial port found!")
        for i in range(len(ports)):
            print(f"{i}: {ports[i]}")
        port = ports[int(input(f"Select port [0-{len(ports) - 1}]:"))]
    else:
        port = ports[0]
    print(f"using {port}")

    with serial.Serial(port, 115200) as serial:

        # arg= int(sys.argv[1])
        arg = 64
        print(f"argument {arg}")
        callstack_size = 2 * (arg + 1) + 2

        print('reading offset')
        await_output(serial, "OFFSET\n", display = False)
        content = read_until(serial, "!\n", display = False)
        content = content.decode()
        print(f"raw offset: {content}")

        offset = content[:-2]
        print(f'decoded offset {offset}')
        offset = int(offset, 16)
        addr = '0x61'

        bp_addr = hex(offset + int(addr, 16))

        ##add breakpoint
        print('adding breakpoint')
        interrupt = bp_addr_helper(offset, addr)
        print(f"sending interrupt {interrupt} and encoded {interrupt.encode()}")
        serial.write(interrupt.encode())

        print(f"waiting for At{bp_addr}!")
        await_output(serial, f'{bp_addr}!\n', display = False)

        ask, locs = ask_debug_session(serial, callstack_size)
        outputfile = 'accumulative_warduino_session_sizes.txt'
        f = open(outputfile , "a")
        f.write(f'arg,callstack,session_size\n')

        for i in range(11):

            if i != 0:
                #step
                print(f"stepping #{i}")
                serial.write('04\n'.encode())
                await_output(serial, "STEP!\n", display = False);
                print("sleep 3 secs so warduino surely stepped")
                time.sleep(3) 
                dump, locs = ask_debug_session(serial, callstack_size)
                print(f'dump_len={len(dump)},locs_len={len(locs)},{len(dump) + len(locs)}\n')
                f.write(f'{arg},{callstack_size},{len(dump) + len(locs)}\n')
        f.close()
