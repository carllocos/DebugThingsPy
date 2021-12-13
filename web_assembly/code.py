from __future__ import annotations
from typing import List, Any, Union
from dataclasses import dataclass, field

from utils import dbgprint, errprint
from web_assembly import SectionDetails, ModuleDetails, DBGInfo


#TODO make code more efficient by overwriting magic functions __lt__, __le__, __gt__, __ge__ and __equal__

@dataclass
class Expr:
    linenr: Union[None, int]
    colstart: Union[None, int]
    colend: Union[None, int]
    addr: str
    exp_type: str
    __code: Union[None, Code] = field(repr=False, init=False, default=None)

    @property
    def code(self) -> Union[Code, None]:
        return self.__code

    @code.setter
    def code(self, c: Code) -> None:
        if isinstance(c, Code):
            self.__code = c

    def copy(self) -> Expr:
        return Expr(self.linenr, self.colstart, self.colend, self.addr, self.exp_type)

    def shift(self):
        e =  Expr(self.linenr, self.colstart, self.colend, self.addr + 1, self.exp_type)
        e.code = self.code
        return e

    def __repr__(self) -> str:
        return f'{str(self)}'

    def __str__(self) -> str:
        return f'<line {self.linenr} ({hex(self.addr)}): {self.exp_type}>'
        
class Code:
    #TODO sort according to linenr, column start
    def __init__(self, func_idx: int, body: List[Expr]) -> Code:
        self.__func_idx = func_idx
        self.__body = body
        self.__ends = None
        self.__code_end = None
        for e in body:
            e.code = self

    @property
    def func_idx(self) -> int:
        return self.__func_idx

    @property
    def expressions(self) -> List[Expr]:
        return self.__body

    @property
    def end(self) -> Expr:
        if self.__code_end is None:
            self.__fill_ends()
        return self.__code_end

    def linenr(self, nr):
        return list(filter(lambda i: i.linenr == nr, self.expressions))

    def addr(self, addr):
        if isinstance(addr, str):
            addr = int(addr, 16)
        return next((e for e in self.expressions if e.addr == addr), None)

    def exp_type(self, exp):
        return list(filter(lambda i: i.exp_type == exp, self.expressions))

    def next_instr(self, exp: Expr) -> Union[None, Expr]:
        return next((e for e in self.expressions if e.addr > exp.addr), None)

    def __fill_ends(self) -> None:
        self.__ends = {}
        ends = list(filter(lambda e: e.exp_type == 'end', self.expressions))
        self.__code_end = ends[-1]
        ends = ends[:-1]
        pos = 0
        if len(ends) > 0:
            ifs = []
            for e in self.expressions:
                if e.exp_type not in ['if', 'loop', 'block', 'else']:
                    continue
                if e.exp_type == 'else':
                    self.__ends[e.addr] =  self.__ends[ifs[-1].addr]
                    ifs = ifs[:-1]
                    if pos >= len(ends) and len(ifs) == 0:
                        break
                    continue

                if e.exp_type == 'if':
                    ifs.append(e)

                self.__ends[e.addr] = ends[pos]
                pos+=1
                if pos >= len(ends) and len(ifs) == 0:
                    break

    def end_expr(self, exp: Expr ) -> Union[None, Expr]:
        if self.__ends is None:
            self.__fill_ends()
        return self.__ends.get(exp.addr, None)

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
        if isinstance(key, str):
            key = int(key, 16)
        if isinstance(key, int):
            return next((c for c in self.codes if c.func_idx == key), None)
        raise ValueError('incorrect key expecting an int')

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
            exps = [ Expr(e.get('line', None), e.get('col_start', None), e.get('col_end', None), e['addr'], e['type'])  for  e in intrs]
            codes_lst.append(Code(func_idx,exps))
        return Codes(codes_lst)