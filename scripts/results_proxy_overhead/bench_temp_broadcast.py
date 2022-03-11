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


def read_until(s: serial.Serial, target: str, display = False):
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


# def read_all(s: serial.Serial):
#     print("READING ALL")
#     content = b''
#     while True:
#         print("in while")
#         b = s.read()
#         if b == b'\r':
#             continue

#         content += b
#         print(content)


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

        runs = 30
        measures = []
        read_until(serial, "c\n") #skip noise
        withProxyInterrupts = len(sys.argv) > 1
        if withProxyInterrupts:
            filename = 'proxy_disturbed.csv'
        else:
            filename = 'proxy_no_disturbed.csv'
        print(f"{runs} in file {filename}")
        for i in range(runs):
            startTime = time.monotonic()
            read_until(serial, "c\n")
            endTime = time.monotonic()
            measures.append(endTime - startTime)


        with open(filename, 'a') as file:
            file.write("delta_time\n")
            for t in measures:
                print(f"time={t}")
                file.write(f"{t}\n")
