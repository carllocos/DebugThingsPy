from __future__ import annotations
from typing import List, Any, Union
from web_assembly import SectionDetails, ModuleDetails, DBGInfo


#TODO make code more efficient by overwriting magic functions __lt__, __le__, __gt__, __ge__ and __equal__

class Expr:

    def __init__(self, linenr: int, colstart: int, colend: int, addr: int, type_expr: str) -> Expr:
       self.__linenr = linenr
       self.__colstart = colstart
       self.__colend = colend
       self.__addr = addr
       self.__type = type_expr
       self.__code = None

    @property
    def linenr(self) -> int:
        return self.__linenr

    @property
    def colstart(self) -> int:
        return self.__colstart

    @property
    def colend(self)-> int:
        return self.__colend

    @property
    def addr(self)-> int:
        return self.__addr

    @property
    def exp_type(self)-> str:
        return self.__type

    @property
    def code(self) -> Union[Code, None]:
        return self.__code

    @code.setter
    def code(self, c: Code) -> None:
        if isinstance(c, Code):
            self.__code = c
        
class Code:
    #TODO sort according to linenr, column start
    def __init__(self, func_idx: int, body: List[Expr]) -> Code:
        self.__func_idx = func_idx
        self.__body = body
        for e in body:
            e.code = self

    @property
    def func_idx(self) -> int:
        return self.__func_idx

    @property
    def expressions(self) -> List[Expr]:
        return self.__body

    def linenr(self, nr):
        return list(filter(lambda i: i.linenr == nr, self.expressions))

    def addr(self, addr):
        if isinstance(addr, str):
            addr = int(addr, 16)
        return next((e for e in self.expressions if e.addr == addr), None)

    def exp_type(self, exp):
        return list(filter(lambda i: i.exp_type == exp, self.expressions))

    def __getitem__(self, key: Any) -> Union[Expr, None]:
        if isinstance(key, int):
            return self.linenr(key)
        elif isinstance(key, str):
            return self.addr(key)
        else:
            raise ValueError(f'incorrect key expecting an int')

class Codes:
    def __init__(self, codes: List[Code]):
        self.__codes = codes

    @property
    def codes(self) -> List[Code]:
        return self.__codes
    
    def __getitem__(self, key: Any) -> Union[Code, None]:
        if isinstance(key, int):
            return next((c for c in self.codes if c.func_idx == key), None)
        else:
            raise ValueError(f'incorrect key expecting an int')

    def addr(self, addr):
        i = None
        for c in self.__codes:
            i = c.addr(addr)
            if i is not None:
                break
        return i

    def linenr(self, nr):
        exps = []
        for c in self.__codes:
            _exps = c.linenr(nr)
            if len(_exps) > 0:
                for e in _exps:
                    exps.append(e)
        return exps
    
    @staticmethod
    def from_dbg(dbg_info: DBGInfo):
        mod : ModuleDetails = dbg_info[1]
        codes = mod['codes']
        codes_lst = []
        for func_idx, intrs in codes.items():
            exps = [ Expr(e['line'], e['col_start'], e['col_end'], e['addr'], e['type'])  for  e in intrs]
            codes_lst.append(Code(func_idx,exps))
        return Codes(codes_lst)