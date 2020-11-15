from enum import Enum


class BreapPoint:

    def __init__(self, module_name, line_number, byte_addr):
        super().__init__()

    def module_name(self):
        return self.__module_name

    def line_number(self):
        return self.__line_number

    def byte_addr(self):
        return self.__byte_addr


class ConstType(Enum):
    I32 = 0
    I64 = 1

    @staticmethod
    def from_str(type_str):
        if len(type_str) == 0 or type_str[0] != 'i':
            raise ValueError('incorrect str. Must be of the form `i32`')
        _bits = int(type_str[1:], 10)
        if _bits % 32 != 0 or _bits > 64:
            raise ValueError('incorrect constant')

        idx = int((_bits / 32) - 1)
        types = [ConstType.I32, ConstType.I64]
        return types[idx]


class StackValues:

    def __init__(self):
        self.__values = []
        self.__idx = None

    def from_idx(self, idx):
        return next(( v for v in self.__values if v['idx'] == idx), False)

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

class Frame:

    def __init__(self, block_type, module, name, idx, fp, sp, ret_addr, func_id):
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

    def set_stack_values(self, sv, callstack):
        self.__stack_values = sv
        self.__callstack = callstack

    def stack_values(self):
        res = {'args': [], 'locals': [], 'rest': []}
        if self.block_type != BlockType.FUNC:
            return res

        func = next(( f for f in self.__callstack.funcs() if f['id'] == self.func_id), False)
        if not func:
            raise ValueError('could not retrieve func')

        args = []
        if func['q_args'] > 0:
            for i in range(1, func['q_args'] + 1):
                args.append(self.__stack_values.from_idx( self.sp + i ))

        _locs = []
        if func['q_locals'] > 0:
            for i in range(1, func['q_locals'] + 1):
                _locs.append(self.__stack_values.from_idx( self.fp + i ))

        next_frame = self.__callstack.find_next(self.idx)
        _vals = self.__stack_values.from_to(self, next_frame)

        _rest = []
        for keep in  _vals:
            if next(( a for a in args if a['idx'] == keep['idx']), False):
                continue
            if next(( l for l in _locs if l['idx'] == keep['idx']), False):
                continue
            _rest.append(keep)

        res['args']= args
        res['locals' ] = _locs
        res['rest' ] = _rest
        return res

    def as_dict(self):
        d =  {'block_type': self.block_type,
              #  'module': self.module,
              #  'name': self.name,
              'fidx': self.func_id,
              'idx': self.idx,
              #  'fp': self.fp,
              #  'sp': self.sp,
              'ret_addr': self.ret_addr
              }
        return d

    def __repr__(self):
        return f'{self.as_dict()}'

    def __str__(self):
        return f'{self.as_dict()}'

class CallStack:
    def __init__(self, funcs, break_point):
        self.__funcs = funcs
        self.__idx = None
        self.__frames = []
        self.__stack_values = False
        self.__other_frames = []
        self.breakpoint = break_point

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
