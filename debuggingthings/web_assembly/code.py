from __future__ import annotations
from typing import List, Any, Union
from web_assembly import SectionDetails, ModuleDetails, DBGInfo

class Expr:

    def __init__(self, linenr: int, colstart: int, colend: int, addr: int, type_expr: str) -> Expr:
       self.__linenr = linenr
       self.__colstart = colstart
       self.__colend = colend
       self.__addr = addr
       self.__type = type_expr
       
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

class Code:

    def __init__(self, func_idx: int, body: List[Expr]) -> Code:
        self.__func_idx = func_idx
        self.__body = body

    @property
    def func_idx(self) -> int:
        return self.__func_idx

    @property
    def expressions(self) -> List[Expr]:
        return self.__body

    def __getitem__(self, key: Any) -> Union[Expr, None]:
        if isinstance(key, int):
            return next((e for e in self.expressions if e.addr == key), None)
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

    @staticmethod
    def from_dbg(dbg_info: DBGInfo):
        mod : ModuleDetails = dbg_info[1]
        codes = mod['codes']
        codes_lst = []
        for func_idx, intrs in codes.items():
            exps = [ Expr(e['line'], e['col_start'], e['col_end'], e['addr'], e['type'])  for  e in intrs]
            codes_lst.append(Code(func_idx,exps))
        return Codes(codes_lst)