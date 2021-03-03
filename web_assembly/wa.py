from web_assembly import stack
from web_assembly import debug_session as DS

from utils import util

#  raw_json =('0x5b', {'dump': {'pc': '0x3ffbec4b', 'start': ['0x3ffbebf0'], 'breakpoints': ['0x3ffbec4b'], 'functions': [{'fidx': '0x0', 'from': '0x3ffbec1d', 'to': '0x3ffbec1d'}, {'fidx': '0x1', 'from': '0x3ffbec20', 'to': '0x3ffbec3a'}, {'fidx': '0x2', 'from': '0x3ffbec3f', 'to': '0x3ffbec50'}], 'callstack': [{'type': 0, 'fidx': '0x2', 'sp': -1, 'fp': -1, 'ra': '0x0'}, {'type': 3, 'fidx': '0x0', 'sp': 0, 'fp': 0, 'ra': '0x3ffbec45'}]}, 'bp': '0x3ffbec4b'}, {'local_dump': {'stack': [{'idx': 0, 'type': 'i32', 'value': 5}, {'idx': 1, 'type': 'i32', 'value': 120}]}, 'bp': '0x3ffbec4b'})
raw_dump = {'dump': {'pc': '0x3ffbecea', 'start': ['0x3ffbebf0'], 'opcode': '0x24 set_global', 'breakpoints': ['0x3ffbecea'], 'functions': [{'fidx': '0x0', 'from': '0x3ffbec53', 'to': '0x3ffbec6e', 'args': 0, 'locs': 3}, {'fidx': '0x1', 'from': '0x3ffbec73', 'to': '0x3ffbec8c', 'args': 0, 'locs': 2}, {'fidx': '0x2', 'from': '0x3ffbec8f', 'to': '0x3ffbec97', 'args': 0, 'locs': 0}, {'fidx': '0x3', 'from': '0x3ffbec9a', 'to': '0x3ffbeca4', 'args': 1, 'locs': 0}, {'fidx': '0x4', 'from': '0x3ffbeca9', 'to': '0x3ffbecec', 'args': 0, 'locs': 5}, {'fidx': '0x5', 'from': '0x3ffbecf1', 'to': '0x3ffbed12', 'args': 0, 'locs': 1}, {'fidx': '0x6', 'from': '0x3ffbed15', 'to': '0x3ffbed2b', 'args': 0, 'locs': 0}, {'fidx': '0x7', 'from': '0x3ffbed2e', 'to': '0x3ffbed3a', 'args': 0, 'locs': 0}], 'callstack': [{'type': 0, 'fidx': '0x7', 'sp': -1, 'fp': -1, 'ra': '0x3ffbec47'}, {'type': 3, 'fidx': '0x0', 'sp': -1, 'fp': 0, 'ra': '0x3ffbed32'}, {'type': 0, 'fidx': '0x4', 'sp': -1, 'fp': 0, 'ra': '0x3ffbed37'}], 'globals': [{'idx': 0, 'type': 'i32', 'value': 0}, {'idx': 1, 'type': 'i32', 'value': 0}, {'idx': 2, 'type': 'i32', 'value': 88}], 'table': {'max': 3, 'elements': [4, 0, 5]}, 'memory': {'pages': 3, 'total': 48, 'bytes': b'\x08\x00\x00\x00\x00\x00\x00\x00_\x00\x00\x00_\x00\x00\x00_\x00\x00\x00_\x00\x00\x00_\x00\x00\x00_\x00\x00\x00_\x00\x00\x00_\x00\x00\x00_\x00\x00\x00\x00\x00\x00\x00'}, 'br_table': {'size': 256, 'labels': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}}, 'bp': '0x3ffbecea'}
raw_locals = {'local_dump': {'stack': [{'idx': 0, 'type': 'i32', 'value': 2}, {'idx': 1, 'type': 'i32', 'value': 95}, {'idx': 2, 'type': 'i32', 'value': 8}, {'idx': 3, 'type': 'i32', 'value': 9}, {'idx': 4, 'type': 'i32', 'value': 9}, {'idx': 5, 'type': 'i32', 'value': 2}]}, 'bp': '0x3ffbecea'}
raw_complex = ('0xfa', raw_dump, raw_locals)



def raw_to_stack(raw):
    if not isinstance(raw, tuple):
        raise ValueError('expects a tuple size 3 (bp, dump, locals)')
    if len(raw) != 3:
        raise ValueError('expects a tuple size 3 (bp, dump, locals)')

    (_bp, _dump_dict, _locals) = raw
    #  print("-----------------------------------------------------------------------------------")
    #  print(f"BReakpoint {_bp}")
    #  print("-----------------------------------------------------------------------------------")
    #  print(f'Locals {_locals}')
    #  print("-----------------------------------------------------------------------------------")
    #  print(f'DUMP {_dump_dict}')

    _dump = _dump_dict['dump']
    _offset =  _dump['start'][0]
    _funcs = [ to_fun(f, _offset) for f in _dump['functions']]
    _cs = stack.CallStack(_funcs, _bp)
    for idx, f in enumerate(_dump['callstack']):
        _frame = to_frame(f, _offset, idx)
        _cs.add_frame(_frame)

    _mem = _dump['memory']
    _mem = stack.Memory(_mem['pages'], _mem['bytes'])
    _tbl = _dump['table']
    _tbl = stack.Table(_tbl['max'], _tbl['elements'])
    __br_table = _dump['br_table']

    _vals = _locals['local_dump']['stack']
    _sv = stack.StackValues()
    for v in _vals:
        _sv.add_value(v['type'], v['value'], v['idx'])

    _cs.set_orignal(_dump)
    _sv.set_orignal(_locals['local_dump'])
    _cs.set_stack_values(_sv)
    _cs.set_memory(_mem)
    _cs.set_table(_tbl)

    _sv.setup()
    _cs.setup()
    kwargs = {
        'callstack': _cs,
        'stack_values':_sv,
        'lin_mem':_mem,
        'table': _tbl,
        'br_table': __br_table,
        'globals': stack.Globals(_dump['globals']),
        #  'opcode':  _dump['opcode']
    }
    return DS.DebugSession(**kwargs)

def to_frame(cs_json, offset, idx):
    _type = stack.BlockType.from_int(cs_json['type'])
    _func_id = int(cs_json['fidx'], 16) if _type == stack.BlockType.FUNC else None
    _module = 'some_mod'
    _name = 'some_name'
    _idx = idx
    _fp = cs_json['fp']
    _sp = cs_json['sp']
    _retaddr = '0x0'
    if cs_json['ra'] != '0x0':
        _retaddr = util.substract_hexs([cs_json['ra'], offset])

    return stack.Frame(_type,_module, _name, _idx, _fp, _sp, _retaddr, _func_id)


def to_fun(fun_json, offset):
    _start_addr = util.substract_hexs([fun_json['from'], offset])
    _end_addr = util.substract_hexs([fun_json['to'], offset])
    _name = 'some_name'
    _module_name= 'module_name'
    _id = int(fun_json['fidx'], 16)
    _qargs = fun_json['args']
    _qlocals = fun_json['locs']
    return stack.make_fun(_module_name, _name, _id, _start_addr, _end_addr, _qargs, _qlocals)

def do_complex():
    return raw_to_stack(raw_complex)

#  def do_test():
#      return raw_to_stack(raw_json)



