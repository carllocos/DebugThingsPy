from __future__ import annotations
from typing import List, Union, Any
from dataclasses import dataclass

from web_assembly import ConstValue

@dataclass
class FunRef:
    fidx: int

    def copy(self) -> FunRef:
        return FunRef(self.fidx)
    

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
        return len(self.__updates) > 0

    def copy(self) -> Table:
        _elems= [ e.copy() for e in self.elements]
        return Table(self.min, self.max, _elems)

    def get_update(self) -> Union[None, Table]:
        if not self.modified:
            return None

        _elems = []
        for e in self.elements:
            if self.__updates.get(e.fidx, False):
                _elems.append(self.__updates[e.fidx])
            else:
                _elems.append(e.copy())

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