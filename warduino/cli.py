from __future__ import annotations
from typing import Union, List, Any
import base64
import functools
import operator
import sys

import binary_protocol as bin_prot
import mylogger as log
import data
import json

#API

def json2binary(state, offset_emulator):
    """
    same as json2binary_and_b64 but returns only the base64 encoded string
    """
    encoding = json2binary_and_b64(state, offset_emulator)
    return encoding['b64']

def json2binary_and_b64(state, offset_emulator):
    """
    generates payload for WARDuino `interruptRecvState`. The interrupt is used to provide WARDuino with a new state (i.e., application and execution state).
    The state 1. is converted into an ordered list of `interruptRecvState` payload strings, 2. the strings are concateneded,
    3. the resulting string is base64 encoded.

    The base64 string is also printed through stdout

    :param state: state that has been extracted from WARDuino through an `interruptWOODDUMP` and that needs to be send to another WARDuino
    :param offset_emulator: the start address of the target WARDuino to where the dump needs to be send
    :return a dictionary containing the base64 encoded string and the list of payloads used to generate the base64 string
    """

    wood_state = rebase_state(state, offset_emulator)
    log.stderr_print(f"State to send {wood_state}")
    payloads = bin_prot.encode_state(wood_state)
    concat_payload = functools.reduce(operator.add, payloads)
    b64_bytes = base64.b64encode(concat_payload.encode("ascii"))
    b64_str = b64_bytes.decode("ascii")
  
    log.stderr_print(f"about to send #{len(payloads)}")
    print(b64_str)

    return {'b64': b64_str, "messages": payloads}


def encode_monitor_proxies(host: str, port: int, func_ids: List[int]) -> str:
    """
    generates payload for WARDuino `interruptMonitorProxies`
    """
    encoding = bin_prot.encode_monitorproxies(host, port, func_ids)
    print(encoding)
    return encoding

## PRIVATE

def rebase_state(_json: dict, target_offset: str) -> dict:
    target_off = int(target_offset, 16)
    offset = int(_json["start"][0], 16)
    rebase = lambda addr : hex( (int(addr, 16) - offset) + target_off)

    br_table = _json['br_table']
    br_table_size = int(br_table['size'], 16)
    _br_labels = br_table['labels']
    if isinstance(_br_labels, list):
        _br_labels = _br_labels[0]
    br_table_labels = bytes2int(_br_labels)

    assert br_table_size == len(br_table_labels), f'expected size {len(br_table_labels)}'

    state = {
        'pc' : rebase(_json['pc']),
        'breakpoints': [rebase(bp) for bp in _json['breakpoints']],
        'br_table': {
            'size': br_table_size,
            'labels': br_table_labels,
            },
        'globals': _json['globals'],
        'table': {
            'init': _json['table']['init'],
            'max': _json['table']['max'],
            'elements' : bytes2int(_json['table']['elements'])
        },
        'memory': {
            'init': _json['memory']['init'],
            'max': _json['memory']['max'],
            'pages': _json['memory']['pages'],
            'bytes': _json['memory']['bytes'],
        },
        'stack': _json['stack'],
    }

    callstack = []
    for frame in _json['callstack']:
        # log.stderr_print(f'Frame {frame}')
        _f = {
            'type': frame['type'],
            'sp': frame['sp'],
            'fp': frame['fp'],
            'ra': frame.get('ra', ''),

            'fidx': frame['fidx'],
            'block_key': frame['block_key'],
            'idx' : frame['idx']
        }
        if _f['ra'] != '':
            _f['ra'] = rebase(_f['ra'])
        if _f['type'] != 0:
            _f['block_key'] = rebase(_f['block_key'])
        callstack.append(_f)

    callstack.sort(key = lambda f: f['idx'], reverse= False)
    state['callstack'] = callstack

    return state

def bytes2int(data):
    ints = []
    for i in range(0, len(data), 4):
        x = int.from_bytes(data[i:i+4],  'little', signed=False)
        ints.append(x)
    return ints

if __name__ == "__main__":
    log.stderr_print(f'args {sys.argv}')
    # print(f'State and Offset of target emulutaro expected {sys.argv[2]}')
    # state = '{"pc":"0x3ffbdbf9","start":["0x3ffbdb70"],"breakpoints":[],"stack":[{"idx":0,"type":"i32","value":0}],"callstack":[{"type":0,"fidx":"0x4","sp":-1,"fp":-1,"block_key":"0x0","ra":"0x3ffbdbdf","idx":0}],"globals":[{"idx":0,"type":"i32","value":23},{"idx":1,"type":"i32","value":1},{"idx":2,"type":"i32","value":0}],"table":{"max":0,"init":0,"elements":[]},"memory":{"pages":0,"max":0,"init":0,"bytes":[]},"br_table":{"size":"0x100","labels":[]}}'
    off = '0x555b341d56a0'
    # json2binary(sys.argv[1], sys.argv[2])
    with open("wood-pull.json", "r") as file:
        content = file.read()
        print(f"type={type(content)}")
        state = json.loads(content)
        # state = json.loads(sys.argv[1])
        # off =  sys.argv[2]
        json2binary(content, off)
