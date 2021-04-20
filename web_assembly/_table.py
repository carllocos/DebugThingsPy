from __future__ import annotations
from typing import List, Union, Any
from dataclasses import dataclass, field


from utils import dbgprint, errprint
from web_assembly import ConstValue, Type

@dataclass
class FunRef:
    __fidx: int = field(repr=False)
    __original: Union[None, FunRef] = field(init=False, repr=False, default= None)

    @property
    def fidx(self) -> int:
        return self.__fidx

    @fidx.setter
    def fidx(self, nidx) -> None:
        if self.__original is None:
            self.__original = self.copy()
        self.__fidx = nidx

    @property
    def original(self) -> Union[None, FunRef]:
        return self.__original

    @property
    def modified(self) -> bool:
        return self.__original is not None

    def get_latest(self) -> FunRef:
        v = self.copy()
        if not self.modified:
            return v

        self.fidx = self.__original.fidx
        self.__original = None
        return v

    def copy(self) -> FunRef:
        return FunRef(self.fidx)

    def __repr__(self) -> str:
        return f'FunRef(fidx={self.fidx})'

#TODO support remove or add elements?
class Table:
    def __init__(self, _min: Union[None, int], _max: Union[int, None] , elements: List[FunRef]):
        self.__min = _min
        self.__max = _max
        self.__elements = elements
        self.__updates = {}

    @property
    def min(self) -> Union[int, None]:
        return self.__min

    @property
    def max(self) -> Union[int, None]:
        return self.__max

    @property
    def elements(self) -> List[FunRef]:
        return self.__elements

    @property
    def modified(self) -> bool:
        return next((e for e in self.elements if e.modified), False) and True
        # return len(self.__updates) > 0

    def copy(self) -> Table:
        _elems= [ e.copy() for e in self.elements]
        return Table(self.min, self.max, _elems)

    def get_update(self, module:Any) -> Union[None, Table]:
        if not self.modified:
            return None

        _elems = []
        for e in self.elements:
            if e.modified:
                org_fidx = e.original.fidx
                new_fidx = e.fidx
                type1 = module.functions[org_fidx].signature
                type2 = module.functions[new_fidx].signature
                if not same_signature(type1, type2):
                    raise ValueError(f'invalid table element: signature change is unallowed. From {type1} to {type2}')
            _elems.append(e.get_latest())

        return Table(self.min, self.max, _elems)

    def __getitem__(self, key: Any) -> FunRef:
        if not isinstance(key, int):
            raise ValueError(f'key error')
        return self.__elements[key]

    def __setitem__(self, key: Any, val: FunRef) -> None:
        if not isinstance(key, int):
            raise ValueError("incorrect key for table assignment")
        v = val if isinstance(val, FunRef) else FunRef(val)
        self.__updates[key] = v

    def __len__(self) -> int:
        return len(self.elements)

    def as_dict(self):
        d = {
            'max': self.__max,
            'elements': self.__elements
            }
        return d

    def __str__(self):
        d = {
            'max': self.__max,
            'elements': self.__elements
            }
        return str(d)

    def __repr__(self):
        return f'{self.as_dict()}'

    def to_json(self) -> dict:
        _json = { 'elements': [e.fidx for e in self.elements] }
        if self.min is not None:
            _json['min'] = self.min

        if self.max is not None:
            _json['max'] = self.max

        return _json

    @staticmethod
    def from_json(_json: dict) -> Table:
        _refs = [ FunRef(e) for e in _json['elements']]
        return Table(_json.get('min', None), _json.get('max', None), _refs)


class Tables:

    def __init__(self, tbls: List[Table]) -> Tables:
        self.__tables = tbls

    def __getitem__(self, key: Any) -> FunRef:
        if not isinstance(key, int):
            raise ValueError(f'key error')
        return self.__tables[key]


def same_signature(type1: Type, type2: Type) -> bool:
    dbgprint(f"comparing {type1} with {type2}")
    if len(type1.parameters) != len(type2.parameters):
        return False
    for e1,e2 in zip(type1.parameters, type2.parameters):
        if e1 != e2:
            return False

    if type1.results is None:
        if type2.results is None:
            return True
        return False
    elif type2.results is None:
        return False
    
    #both are lists
    if len(type1.results) != len(type2.results):
        return False

    for r1,r2 in zip(type1.results, type2.results):
        if r1 != r2:
            return False
    return True