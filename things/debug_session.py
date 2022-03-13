from __future__ import annotations
from typing import Union, List

from utils import dbgprint, errprint
from boards import Device
from web_assembly import WAModule, CallStack, Stack, Table, Memory, Globals, Expr

class DebugSession(object):

    def __init__(self, **kwargs): 
        self.__module = kwargs['module']
        self.__pc = kwargs['pc']
        self.__cs = kwargs['callstack']
        self.__sv = kwargs['stack']
        self.__memory = kwargs['memory']
        self.__table = kwargs['table']
        self.__br_table = kwargs['br_table']
        self.__globals = kwargs['globals']
        self.__device = kwargs['device']
        self.__exception = None
        self.__instr = None
        self.__valid = None
        self.__version = None
        self.__pc_error = kwargs.get('pc_error', None)
        self.__breakpoints= kwargs['breakpoints']

        #TODO remove
        self.__totalsize = kwargs.get('session_size', None)

    @property
    def total_size(self) -> Union[int, None]:
        #TODO remove
        print(f'SESSION SIZE {self.__totalsize}')
        return self.__totalsize

    @property
    def breakpoints(self) -> List[str]:
        return [ self.module.addr(bp) for bp in self.__breakpoints]

    @property
    def version(self) -> Union[int, None]:
        return self.__version

    @version.setter
    def version(self, v: int) -> None:
        if self.__version is not None:
            raise ValueError('cannot change the version of an already registered session')
        self.__version = v

    @property
    def pc_error(self) -> Union[Expr, None]:
        if isinstance(self.__pc_error, str):
            m  = self.__module
            i = m.codes.addr(self.__pc_error)
            if i is not None:
                self.__pc_error = i
        return self.__pc_error

    @property
    def exception(self) -> Union[str, None]:
        return self.__exception
    
    @exception.setter
    def exception(self, excp_msg: str) -> None:
        self.__exception = excp_msg

    @property
    def module(self) -> WAModule:
        return self.__module

    @property
    def device(self) -> Device:
        return self.__device

    @property
    def callstack(self) -> CallStack:
        return self.__cs

    @property
    def stack(self) -> Stack:
        return self.__sv

    @property
    def memory(self) -> Memory:
        return self.__memory

    @property
    def table(self) -> Table:
        return self.__table

    @property
    def br_table(self) -> List[int]:
        return self.__br_table

    @property
    def globals(self) -> Globals:
        return self.__globals

    @property
    def pc(self) -> Union[Expr, None]:
        if self.__instr is None:
            m  = self.__module
            i = m.codes.addr(self.__pc)
            if i is None:
                i = self.__pc
            self.__instr = i
        return self.__instr

    @property
    def modified(self) -> bool:
        if self.stack.modified:
            return True
        elif self.callstack.modified:
            return True
        elif self.table.modified:
            return True
        elif self.memory.modified:
            return True
        elif self.table.modified:
            return True
        elif self.globals.modified:
            return True
        else:
            return False

    def validate(self) -> None:
        dbgprint("TODO validate the change")

    @property
    def valid(self) -> bool:
        if self.__valid is None:
            #TODO ad try catch
            self.validate()
            self.__valid = True
        return self.__valid

    def get_update(self) -> Union[None, DebugSession]:
        if not self.modified:
            return None

        new_state = {
            'callstack': self.callstack,
            'stack':self.stack,
            'memory':self.memory,
            'table': self.table,
            'globals': self.globals,
        }

        for key in new_state.keys():
            obj = new_state[key]
            upd = obj.get_update(self.module)
            if upd is None:
                new_state[key] = obj.copy()
            else:
                new_state[key] = upd

        new_state['pc'] = self.pc
        new_state['module'] = self.module
        new_state['device'] = self.device
        new_state['br_table'] = self.br_table

        return DebugSession(**new_state)

    def to_json(self) -> dict:
        pc = hex(self.pc.addr)
        stack = self.stack.to_json()['stack']
        callstack = self.callstack.to_json()['callstack']

        memory = self.memory.to_json()
        tbl = self.table.to_json()
        _globals = self.globals.to_json()['globals']
        br_table = self.br_table
        _pc_error = self.pc_error

        if isinstance(_pc_error, Expr):
           _pc_error = _pc_error.addr
        elif _pc_error is not None and isinstance(_pc_error, str):
            errprint(f"_pc_error is not appropriate type. type is {type(_pc_error)}")

        _json = {
            'pc': pc,
            'callstack': callstack,
            'stack': stack,
            'memory': memory,
            'table': tbl,
            'br_table': br_table,
            'globals': _globals,
            'breakpoints': self.__breakpoints,
            'pc_error': _pc_error
        }

        return _json

    @staticmethod
    def from_json(_json: dict, module: WAModule, device: Device) -> DebugSession:
        pc = _json['pc']
        stack = Stack.from_json_list(_json['stack'])

        callstack = CallStack.from_json(_json['callstack'])
        callstack.stack = stack
        callstack.module = module

        memory = Memory.from_json(_json['memory'])
        tbl = Table.from_json(_json['table'])
        _globals = Globals.from_json_list(_json['globals'])
        br_table = _json['br_table']

        kwargs = {
            'module': module,
            'pc': pc,
            'callstack': callstack,
            'stack': stack,
            'memory': memory,
            'table': tbl,
            'br_table': br_table,
            'globals': _globals,
            'device': device,
            'breakpoints': _json['breakpoints'], 
        }

        if _json.get('pc_error', None) is not None:
            kwargs['pc_error'] = _json['pc_error']
        if _json.get('session_size', None) is not None:
            kwargs['session_size'] = _json['session_size']

        return DebugSession(**kwargs)
