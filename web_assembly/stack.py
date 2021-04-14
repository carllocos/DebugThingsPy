from enum import Enum
import struct as struct #https://www.delftstack.com/howto/python/how-to-convert-bytes-to-integers/


# class BreapPoint:

#     def __init__(self, module_name, line_number, byte_addr):
#         super().__init__()

#     def module_name(self):
#         return self.__module_name

#     def line_number(self):
#         return self.__line_number

#     def byte_addr(self):
#         return self.__byte_addr


class ConstType(Enum):
    I32 = 0
    I64 = 1
    F32 = 2
    F64 = 3


    @staticmethod
    def from_str(type_str):
        types = ['i32', 'i64', 'f32', 'f64']
        idx =  next((idx for idx, t in enumerate(types) if type_str == t), None)

        if idx is None:
            raise ValueError(f'incorrect str. Must be of the form `i32`. Given {type_str}')

        types = [ConstType.I32, ConstType.I64, ConstType.F32, ConstType.F64]
        return types[idx]


class StackValues:

    def __init__(self):
        self.__values = []
        self.__idx = None

    def from_idx(self, idx): # TODO BUG FIX False
        r =  next(( v for v in self.__values if v['idx'] == idx), False)
        if isinstance(r, bool):
            raise ValueError(f"Did not find stack value with idx {idx}")
        return r

    def from_to(self, frame, next_frame = False):
        if not next_frame:
            return [ v for v in self.__values if v['idx'] > frame.sp]
        else:
            return [ v for v in self.__values if v['idx'] > frame.sp and v['idx'] <= next_frame.sp]


    def next_val(self):
        if self.__idx is None or self.__idx >= len(self.__values):
            self.__idx = None
            return False
        v = self.__values[self.__idx]
        self.__idx += 1
        return v

    def reset_iterator(self):
        self.__idx = 0

    def setup(self):
        self.reset_iterator()
        self.__values.sort(key = lambda sv: sv['idx'], reverse= True)

    def add_value(self, type_str, val, idx):
        v = StackValues.stack_value(type_str, val, idx)
        self.__values.append(v)

    def set_orignal(self, org):
        self.original = org

    def print(self):
        s = ''
        for v in self.__values:
            s = s + str(v) + '\n'
        print(s)

    @staticmethod
    def stack_value(type_str, val, idx):
        return {'type': ConstType.from_str(type_str), 'value': val, 'idx': idx}

class BlockType(Enum):
    FUNC = 0
    INIT_EXP = 1
    BLOCK = 2
    LOOP = 3
    IF = 4

    @staticmethod
    def from_int(i):
        if not isinstance(i, int):
            raise ValueError('integer expected')

        types = [BlockType.FUNC, BlockType.INIT_EXP, BlockType.BLOCK, BlockType.LOOP, BlockType.IF]
        if i >= len(types):
            raise ValueError(f'incorrect BlockType idx {i}')
        return types[i]

    @staticmethod
    def tostr(bt):
        if bt == BlockType.FUNC:
            return 'func'
        elif bt == BlockType.INIT_EXP:
            return 'init_exp'
        elif bt == BlockType.BLOCK:
            return 'block'
        elif bt == BlockType.LOOP:
            return 'loop'
        elif bt == BlockType.IF:
            return 'if'
        else:
            return 'unknow'

class CleanedStackValues:

    def __init__(self, vals):
        super().__init__()
        self.__vals = vals
        self.__vals.sort(key = lambda sv: sv['idx'], reverse= True)
        self.__iterator = len(vals) - 1

    @property
    def values(self):
        return self.__vals

    def pop(self):
        v = False
        if self.__iterator < len(self.__vals):
            v = self.__vals[self.__iterator]
            self.__iterator = self.__iterator + 1
        return v

    def reset(self):
        self.__iterator = len(self.__vals) - 1
class Locals:

    def __init__(self, locs):
        super().__init__()
        self.__locs = locs

    def __str__(self):
        return str(self.__locs)

    def __repr__(self):
        return str(self.__locs)

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise ValueError('Key must be integer')

        return next((l for l in self.__locs if l['idx'] == key), False)

    #  def get(self, idx=None):
    #      v = False
    #      if idx is not None:
    #          v = next((l for l in self.__locs if l['idx'] == idx), False)
    #      return v

class Frame:

    def __init__(self, block_type, module, name, idx, fp, sp, ret_addr, func_id, block_key):
        self.block_type = block_type
        self.module = module
        self.name = name
        self.idx = idx
        self.fp = fp
        self.sp = sp
        self.ret_addr = ret_addr
        self.func_id =func_id
        self.__stack_values = False
        self.__callstack = False
        self.__cleaned_sv = False
        self.__locals = False
        self.__args = False
        self.__block_key = block_key

    @property
    def locals(self):
        if not self.__locals:
            self.stack_values()
        return self.__locals

    @property
    def args(self):
        if not self.__args:
            self.stack_values()
        return self.__args

    def set_stack_values(self, sv, callstack):
        self.__stack_values = sv
        self.__callstack = callstack

    def org_stack_vals(self):
        return self.__stack_values

    def stack_values(self):
        if self.__cleaned_sv:
            return self.__cleaned_sv

        res = {'args': [], 'locals': [], 'rest': []}
        if self.block_type != BlockType.FUNC:
            return res

        func = next(( f for f in self.__callstack.funcs() if f['id'] == self.func_id), False)
        if not func:
            raise ValueError('could not retrieve func')


        fp = self.sp + 1 #start of fp of current function call sp is the sp prior the call of f i.e. one position before args start
        args = []
        if func['q_args'] > 0:
            for i in range(0, func['q_args']):
                args.append(self.__stack_values.from_idx( fp + i ))

        _locs = []
        sp_locs = fp + func['q_args']
        if func['q_locals'] > 0:
            for i in range(func['q_locals']):
                _locs.append(self.__stack_values.from_idx( sp_locs + i ))

        next_frame = self.__callstack.find_next(self.idx)
        _vals = self.__stack_values.from_to(self, next_frame)

        _rest = []
        for keep in  _vals:
            #  print(f'KEEP {keep}')
            #  print(f'ARGS {args}')
            if next(( a for a in args if a['idx'] == keep['idx']), False):
                continue
            #  print(f'LOCALS {_locs}')
            if next(( l for l in _locs if l['idx'] == keep['idx']), False):
                continue
            _rest.append(keep)

        self.__args = args
        self.__locals = Locals(_locs)
        self.__cleaned_sv = CleanedStackValues(_rest)
        return self.__cleaned_sv

    def as_dict(self):
        _func = self.module.functions[self.func_id]
        _fn = _func.any_name()
        d =  {
              'fidx': self.func_id,
              'fp': self.fp,
              'sp': self.sp,
              'return': self.ret_addr,
              }
        if _fn is not None:
            d['fun_name'] = _fn
        _ra = self.module.addr(self.ret_addr)
        if _ra is not None:
            d['return']  = str(_ra)
        return d

    def __repr__(self):
        return f'{self.as_dict()}'

    def __str__(self):
        return f'{self.as_dict()}'

class Memory:
    def __init__(self, pages, byts):
        self.__pages = pages
        self.__bytes = byts

    def __str__(self):
        d = {
            'pages': self.__pages,
            'bytes': self.__bytes
            }
        return str(d)

    def as_dict(self):
        d = {
            'pages': self.pages,
            'bytes': self.bytes
            }
        return d

    def __repr__(self):
        return f'{self.as_dict()}'

    @property
    def bytes(self):
        return self.__bytes

    @property
    def pages(self):
        return self.__pages

    def to_4bytes_ints(self):
        qe = len(self.bytes) // 4
        #  print(f"quantity elements {qe}")
        _ints = []

        for i in range(qe):
            off = i * 4
            _b = self.bytes [off : off + 4]
            (_int, _ ) = struct.unpack('<HH', _b)
            _ints.append(_int)

        return _ints

class Table:
    def __init__(self, max_elements, elements):
        self.__max = max_elements
        self.__elements = [ {'fidx': e} for e in elements]

    def __str__(self):
        d = {
            'max': self.__max,
            'elements': self.__elements
            }
        return str(d)

    def as_dict(self):
        d = {
            'max': self.__max,
            'elements': self.__elements
            }
        return d

    def __repr__(self):
        return f'{self.as_dict()}'

    def get_elements(self):
        return self.__elements

class CallStack:
    def __init__(self, funcs, pc):
        self.__funcs = funcs
        self.__idx = None
        self.__frames = []
        self.__stack_values = False
        self.__other_frames = []
        self.pc = pc
        self.__memory = False
        self.__table = False

    def set_memory(self, mem):
        self.__memory = mem

    def get_memory(self):
        return self.__memory

    def set_table(self, table):
        self.__table = table

    def get_table(self):
        return self.__table

    def values(self):
        return self.__stack_values

    def pop_frame(self, skip=0):
        if skip > 0 and self.__idx is not None:
            self.__idx += skip

        if self.__idx is None or self.__idx >= len(self.__frames):
            self.__idx = None
            return False

        f = self.__frames[self.__idx]
        self.__idx += 1
        return f

    def has_next(self):
        return self.__idx is not None and self.__idx < len(self.__frames)

    def find_next(self, frame_id):
        next = False
        for f in self.__frames:
            if f.idx == frame_id:
                break
            next = f
        return next

    def reset_iterator(self):
        self.__idx = 0

    def setup(self):
        self.__frames.sort(key = lambda f: f.idx, reverse= True)
        self.__other_frames.sort(key = lambda f: f.idx, reverse= True)
        for f in self.__frames:
            f.set_stack_values(self.__stack_values, self)
        for f in self.__other_frames:
            f.set_stack_values(self.__stack_values, self)

        self.reset_iterator()

    def add_frame(self, frame):
        if frame.block_type == BlockType.FUNC:
            self.__frames.append(frame)
        else:
            self.__other_frames.append(frame)

    def set_orignal(self, org):
        self.original = org

    def funcs(self):
        return self.__funcs

    def set_stack_values(self, sv):
        self.__stack_values = sv

    def print(self):
        s = ''
        for f in self.__frames:
            s = s + str(f) + '\n'
        print(s)

def make_fun(module, name, func_id, from_addr, to_addr, args_amounts, locals_amount):
    f = {'id': func_id,
         'start_addr':from_addr,
         'end_addr':to_addr,
         #  'module': module,
         #  'name': name,
         'q_args': args_amounts,
         'q_locals': locals_amount}
    return f

class Globals:
    def __init__(self, _globals):
        self.__globals = _globals

    def __str__(self):
        return str(self.__globals)

    def __repr__(self):
        return str(self)

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise ValueError('Key must be integer')

        return next((g for g in self.__globals if g['idx'] == key), False)
