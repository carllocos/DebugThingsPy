from __future__ import annotations
from typing import Union, List
from dataclasses import dataclass, field
from enum import Enum

from utils import dbgprint, errprint
from web_assembly import WAModule, Stack, StackValue


@dataclass
class Frame:
    idx: int
    block_type: str
    __fp: int = field(repr=False) #fp of previous frame
    sp: int = field(repr=False) #sp of preivous frame
    ret_addr: str
    fun_idx: Union[int, None] = None
    __block_key: Union[None, str] = field(init=False, repr=False, default=None)
    module: Union[WAModule, None] = field(init = False, repr=False, default=None)
    stack: Union[Stack, None] = field(repr=False, default = None)

    @property
    def fp(self) -> Union[int, None]:
        if self.block_type != 'fun':
            return None
        return self.sp + 1

    @property
    def prev_fp(self) -> int:
        return self.__fp

    @property
    def block_key(self) -> Union[str, None]:
        return self.__block_key

    @block_key.setter
    def block_key(self, key: str) -> None:
        self.__block_key = key
    
    @property
    def locals(self) -> List[StackValue]:
        if self.block_type != 'fun':
            return []
        elif self.stack is None or self.module is None:
            raise ValueError('Module required to generate args')

        fun = self.module.functions[self.fun_idx]
        args_amount = len(fun.signature.parameters)
        locals_amount = len(fun.locals)
        keys = map(lambda loc: loc.idx , fun.locals )
        locals_dict = dict(zip(keys, fun.locals))
        fp = self.fp
        sp = fp + args_amount
        values = self.stack[sp : sp + locals_amount]
        for v in values:
           _loc = locals_dict[v.idx]
           v.name = _loc.name
        return values

    @property
    def args(self) -> List[StackValue]:
        if self.block_type != 'fun':
            return []
        elif self.stack is None or self.module is None:
            raise ValueError('Module required to generate args')

        fp = self.fp
        fun = self.module.functions[self.fun_idx]
        args_amount = len(fun.signature.parameters)
        return self.stack[fp : fp + args_amount]

    def to_json(self) -> dict:
        _json =  {
            'idx': self.idx,
            'block_type': self.block_type,
            'sp': self.sp,
            'fp': self.prev_fp,
            'ret_addr': self.ret_addr,
            'fidx': 0 if self.fun_idx is None else self.fun_idx
        }
        if self.block_type != 'fun':
            _json['block_key'] = self.block_key
        return _json

    @staticmethod
    def from_json(_json: dict) -> Frame:
        f = Frame(_json['idx'], _json['block_type'], _json['fp'], _json['sp'], _json['ret_addr'], _json.get('fidx', None))
        if f.block_type != 'fun':
            f.block_key = _json['block_key']
        return f

@dataclass
class CallStack:
    __frames: List[Frame]
    __idx: int = field(repr=False, init=False, default = int(0))
    __len: int = field(repr=False, init=False, default = int(0))
    __stack: Union[Stack, None] = field(repr=False, init=False, default=None)
    __module: Union[WAModule, None] = field(repr=False, init=False, default=None)

    def __post_init__(self):
        self.__idx = 0
        self.__frames.sort(key = lambda f: f.idx, reverse= True)
        self.__len = len(self.frames)

    @property
    def stack(self) -> Union[Stack, None]:
        return self.__stack

    @stack.setter
    def stack(self, s) -> None:
        for f in self.frames:
            f.stack = s
        self.__stack = s

    @property
    def module(self) -> Union[WAModule, None]:
        return self.__module

    @module.setter
    def module(self, m: WAModule) -> None:
        for f in self.frames:
            f.module = m
        self.__module = m

    @property
    def frames(self) -> List[Frame]:
        return list(filter(lambda f: f.block_type == 'fun', self.__frames))

    @property
    def all_frames(self) -> List[Frame]:
        return self.__frames

    def pop_frame(self, skip=0) -> Union[Frame, None]:
        if skip > 0:
            self.__idx += skip

        if self.__idx >= len(self):
            return None

        f = self.frames[self.__idx]
        self.__idx += 1
        return f

    def get_update(self) -> Union[None, CallStack]:
        return None

    def has_next(self) -> bool:
        return self.__idx < len(self)

    def __len__(self) -> int:
        return self.__len

    def reset_iterator(self):
        self.__idx = 0

    @property
    def modified(self) -> bool:
        return False

    def print(self):
        s = ''
        for f in self.frames:
            s = s + str(f) + '\n'
        print(s)

    def to_json(self) -> List[dict]:
        return {'callstack': [f.to_json() for f in self.__frames] }

    @staticmethod
    def from_json(_json: dict) -> CallStack:
        frames = []
        for idx, frame_obj in enumerate(_json):
            frame_obj['idx'] = idx
            frames.append(Frame.from_json(frame_obj))
        return CallStack(frames)