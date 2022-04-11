import base64

import binary_protocol as bin_prot
import mylogger as log

def request_state():
    return {"pc":"0x60000310809c","start":["0x600003108000"],"breakpoints":[],"stack":[{"idx":0,"type":"i32","value":1000}],"callstack":[{"type":0,"fidx":"0x4","sp":-1,"fp":-1,"block_key":"0x0", "ra":"0x60000310806f", "idx":0},{"type":3,"fidx":"0x0","sp":0,"fp":0,"block_key":"0x600003108090", "ra":"0x600003108092", "idx":1}],"globals":[{"idx":0,"type":"i32","value":23},{"idx":1,"type":"i32","value":1},{"idx":2,"type":"i32","value":0}],"table":{"max":0, "init":0, "elements":[]},"memory":{"pages":0,"max":0,"init":0,"bytes":[]},"br_table":{"size":"0x100","labels":[]}}

#base 64
def json2binary(state, offset_emulator):

    bytes_per_msg = 1000
    wood_state = rebase_state(state, offset_emulator)
    log.stderr_print(f"State to send {wood_state}")

    messages = bin_prot.encode_session(wood_state, bytes_per_msg)
    messages.reverse()
    _long_msg = ''
    for m in messages:
        _msg = m + '\n'
        log.stderr_print(f'msg to send: {_msg}')
        _long_msg += _msg
    b64_bytes = base64.b64encode(_long_msg.encode("ascii"))
    b64_str = b64_bytes.decode("ascii")
  
    log.stderr_print(f"about to send #{len(messages)}")
    log.stderr_print(f'long msg: {_long_msg}')
    log.stderr_print(f"Base 64 Encoded string: {b64_str}")

def rebase_state(_json: dict, target_offset: str) -> dict:
    target_off = int(target_offset, 16)
    offset = int(_json["start"][0], 16)
    rebase = lambda addr : hex( (int(addr, 16) - offset) + target_off)

    state = {
        'pc' : rebase(_json['pc']),
        'breakpoints': [rebase(bp) for bp in _json['breakpoints']],
        'br_table': {
            'size': len(_json['br_table']),
            'labels': _json['br_table'],
            },
        'globals': _json['globals'],
        'table': {
            'init': _json['table'].get('min', 0),
            'max': _json['table'].get('max', 0),
            'elements' : _json['table']['elements']
        },
        'memory': {
            'init': _json['memory'].get('min', 0),
            'max': _json['memory'].get('max', 0),
            'pages': _json['memory']['pages'],
            'bytes': _json['memory']['bytes'],
        },
        'stack': _json['stack'],
    }

    # _frame_types = {
    #     'fun': 0,
    #     'init_exp': 1,
    #     'block': 2,
    #     'loop': 3,
    #     'if': 4
    # }

    callstack = []
    for frame in _json['callstack']:
        _f = {
            'idx' : frame['idx'],
            'type': frame['type'],
            'fidx': frame.get('fidx'),# 0),
            'sp': frame['sp'],
            'fp': frame['fp'],
            'ra': frame.get('ret_addr', ''),
            'block_key': frame.get('block_key', '')
        }
        if frame.get('ret_addr', False):
            _f['ra'] = rebase(frame['ret_addr'])
        if frame.get('block_key', False):
            _f['block_key'] = rebase(frame['block_key'])
        callstack.append(_f)

    callstack.sort(key = lambda f: f['idx'], reverse= False)
    state['callstack'] = callstack

    return state


def test():
    json2binary(request_state(), "0x00")

if __name__ == "__main__":
    test()
else:
    print("no main")
            

