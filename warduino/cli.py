import base64

import binary_protocol as bin_prot
import mylogger as log
import data
import sys

#base 64
def json2binary(state, offset_emulator):
    encoding = son2binary_and_b64(state, offset_emulator)
    return encoding['b64']

def json2binary_and_b64(state, offset_emulator):

    bytes_per_msg = 1000
    wood_state = rebase_state(state, offset_emulator)
    log.stderr_print(f"State to send {wood_state}")

    messages = bin_prot.encode_session(wood_state, bytes_per_msg)

    messages.reverse()
    _long_msg = ''
    complete_messages = []
    for m in messages:
        _msg = m + bin_prot.END_MSG
        complete_messages.append(_msg)
        _long_msg += _msg
    b64_bytes = base64.b64encode(_long_msg.encode("ascii"))
    b64_str = b64_bytes.decode("ascii")
  
    log.stderr_print(f"about to send #{len(messages)}")
    # log.stderr_print(f'long msg: {_long_msg}')
    # log.stderr_print(f"Base 64 Encoded string: {b64_str}")
    print(b64_str) # TODO uncomment

    complete_messages.reverse()
    return {'b64': b64_str, "messages": complete_messages}


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

    # _frame_types = {
    #         0: 'fun',
    #         1: 'init_exp',
    #         2: 'block',
    #         3: 'loop',
    #         4: 'if'
    #     }
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

            'fidx': frame['fidx'],# 0),
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
    assert len(sys.argv) == 2, 'Offset of target emulutaro expected'
    json2binary(data.fac_state(), sys.argv[1])

