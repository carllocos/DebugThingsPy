from . import encoder

Interrupts = {
    'addbp': '06',
    'dump': '60',
    'offset': '0x61',
    'locals': '11',
    'receivesession': '62',
    'recvproxies': '25',
    'rmvbp': '07',
    'run': '01',
    'step': '04',
    'until': '05',
    'updateModule' : '24',
    'pause': '03'
}

#base 64

def json2binary(state, offset_emulator):
    recv_int = Interrupts['receivesession']
    wood_state = rebase_state(session, offset_emulator)
    dbgprint(f"State to send {wood_state}")
    sers = encoder.serialize_session(wood_state, recv_int, self.max_bytes)
    msgs = []
    l = len(sers)
    assert l >= 2, f'at least two expected got {l}'
    _encoded = ''
    for s in reverse(sers):
        _encoded += (s + '\n')
    print(_encoded.encode("base64"))
    
    # for idx, content in enumerate(sers):
     #   rpl = receive_done_session if (idx + 1) == l else receive_ack
        #print(content + '\n', rpl)

    dbgprint(f"about to send #{len(msgs)}")
    #replies = self.medium.send(msgs)

    #return replies[-1]

# TODO still remove old offset
def rebase_state(_json: dict, offset: str) -> dict:
    _offset = int(offset, 16)
    rebase = lambda addr : hex( int(addr, 16) + _offset)

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

    _frame_types = {
        'fun': 0,
        'init_exp': 1,
        'block': 2,
        'loop': 3,
        'if': 4
    }

    callstack = []
    for frame in _json['callstack']:
        _f = {
            'idx' : frame['idx'],
            'type': _frame_types[frame['block_type']],
            'fidx': hex(frame.get('fidx', 0)),
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
