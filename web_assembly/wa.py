from web_assembly import stack

from utils import util

raw_json =('0x5b', {'dump': {'pc': '0x3ffbec4b', 'start': ['0x3ffbebf0'], 'breakpoints': ['0x3ffbec4b'], 'functions': [{'fidx': '0x0', 'from': '0x3ffbec1d', 'to': '0x3ffbec1d'}, {'fidx': '0x1', 'from': '0x3ffbec20', 'to': '0x3ffbec3a'}, {'fidx': '0x2', 'from': '0x3ffbec3f', 'to': '0x3ffbec50'}], 'callstack': [{'type': 0, 'fidx': '0x2', 'sp': -1, 'fp': -1, 'ra': '0x0'}, {'type': 3, 'fidx': '0x0', 'sp': 0, 'fp': 0, 'ra': '0x3ffbec45'}]}, 'bp': '0x3ffbec4b'}, {'local_dump': {'stack': [{'idx': 0, 'type': 'i32', 'value': 5}, {'idx': 1, 'type': 'i32', 'value': 120}]}, 'bp': '0x3ffbec4b'})
raw_dump = {'dump': {'pc': '0x3ffbec37', 'start': ['0x3ffbebf0'], 'breakpoints': ['0x3ffbec37'], 'functions': [{'fidx': '0x0', 'from': '0x3ffbec1d', 'to': '0x3ffbec1d', 'args': 1, 'locs': 0}, {'fidx': '0x1', 'from': '0x3ffbec20', 'to': '0x3ffbec3a', 'args': 2, 'locs': 0}, {'fidx': '0x2', 'from': '0x3ffbec3f', 'to': '0x3ffbec50', 'args': 0, 'locs': 1}], 'callstack': [{'type': 0, 'fidx': '0x2', 'sp': -1, 'fp': -1, 'ra': '0x0'}, {'type': 3, 'fidx': '0x0', 'sp': 0, 'fp': 0, 'ra': '0x3ffbec45'}, {'type': 0, 'fidx': '0x1', 'sp': 0, 'fp': 0, 'ra': '0x3ffbec4b'}, {'type': 4, 'fidx': '0x0', 'sp': 3, 'fp': 1, 'ra': '0x3ffbec27'}, {'type': 0, 'fidx': '0x1', 'sp': 2, 'fp': 1, 'ra': '0x3ffbec33'}, {'type': 4, 'fidx': '0x0', 'sp': 5, 'fp': 3, 'ra': '0x3ffbec27'}, {'type': 0, 'fidx': '0x1', 'sp': 4, 'fp': 3, 'ra': '0x3ffbec33'}, {'type': 4, 'fidx': '0x0', 'sp': 7, 'fp': 5, 'ra': '0x3ffbec27'}, {'type': 0, 'fidx': '0x1', 'sp': 6, 'fp': 5, 'ra': '0x3ffbec33'}, {'type': 4, 'fidx': '0x0', 'sp': 9, 'fp': 7, 'ra': '0x3ffbec27'}, {'type': 0, 'fidx': '0x1', 'sp': 8, 'fp': 7, 'ra': '0x3ffbec33'}, {'type': 4, 'fidx': '0x0', 'sp': 11, 'fp': 9, 'ra': '0x3ffbec27'}]}, 'bp': '0x3ffbec37'}
raw_locals = {'local_dump': {'stack': [{'idx': 0, 'type': 'i32', 'value': 5}, {'idx': 1, 'type': 'i64', 'value': 13}, {'idx': 2, 'type': 'i32', 'value': 5}, {'idx': 3, 'type': 'i64', 'value': 14}, {'idx': 4, 'type': 'i32', 'value': 4}, {'idx': 5, 'type': 'i64', 'value': 15}, {'idx': 6, 'type': 'i32', 'value': 3}, {'idx': 7, 'type': 'i64', 'value': 16}, {'idx': 8, 'type': 'i32', 'value': 2}, {'idx': 9, 'type': 'i64', 'value': 17}, {'idx': 10, 'type': 'i32', 'value': 1}]}, 'bp':'0x3ffbec37 '}
raw_complex = ('0x47', raw_dump, raw_locals)



def raw_to_stack(raw):
    if not isinstance(raw, tuple):
        raise ValueError('expects a tuple size 3 (bp, dump, locals)')
    if len(raw) != 3:
        raise ValueError('expects a tuple size 3 (bp, dump, locals)')

    (_bp, _dump_dict, _locals) = raw
    _dump = _dump_dict['dump']
    _offset =  _dump['start'][0]
    _funcs = [ to_fun(f, _offset) for f in _dump['functions']]
    _cs = stack.CallStack(_funcs)
    for idx, f in enumerate(_dump['callstack']):
        _frame = to_frame(f, _offset, idx)
        _cs.add_frame(_frame)

    _cs.set_orignal(_dump)
    _vals = _locals['local_dump']['stack']
    _sv = stack.StackValues()
    for v in _vals:
        _sv.add_value(v['type'], v['value'], v['idx'])

    _sv.set_orignal(_locals['local_dump'])
    return (_bp, _cs, _sv)

def to_frame(cs_json, offset, idx):
    _type = stack.BlockType.from_int(cs_json['type'])
    _func_id = cs_json['fidx'] if _type == stack.BlockType.FUNC else None
    _module = 'some_mod'
    _name = 'some_name'
    _idx = idx
    _fp = cs_json['fp'] if cs_json['fp'] != -1 else None
    _sp = cs_json['sp'] if cs_json['sp'] != -1 else None
    _retaddr = None
    if cs_json['ra'] != '0x0':
        _retaddr = util.substract_hexs([cs_json['ra'], offset])

    return stack.Frame(_type,_module, _name, _idx, _fp, _sp, _retaddr, _func_id)


def to_fun(fun_json, offset):
    _start_addr = util.substract_hexs([fun_json['from'], offset])
    _end_addr = util.substract_hexs([fun_json['to'], offset])
    _name = 'some_name'
    _module_name= 'module_name'
    _id = fun_json['fidx']
    _qargs = fun_json['args']
    _qlocals = fun_json['locs']
    return stack.make_fun(_module_name, _name, _id, _start_addr, _end_addr, _qargs, _qlocals)

def do_complex():
    return raw_to_stack(raw_complex)

def do_test():
    return raw_to_stack(raw_json)



