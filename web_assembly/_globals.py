from __future__ import annotations
from typing import Union, List

from web_assembly import ConstValue
ValType = Union[float, int]

class GlobalValue(ConstValue):
    def __init__(self, type_str: str, val: ValType, mutable: bool = False) -> GlobalValue:
        super().__init__(type_str, val)
        self.__mutable = mutable
        self.__update = None

    @property
    def mutable(self) -> bool:
        return self.__mutable

    @property
    def modified(self) -> bool:
        return self.__update is not None

    def _set_value(self, v: ValType) -> None:
        self.__update = GlobalValue(self.type, v, self.mutable)
    
    def to_json(self) -> dict:
        return {
            'type' : self.type,
            'value': self.value
        }

    @staticmethod
    def from_json(_json: dict) -> GlobalValue:
        return GlobalValue(_json['type'], _json['value'])

class Globals:
    def __init__(self, _globals: List[GlobalValue]):
        self.__globals = _globals

    @property
    def values(self) -> List[GlobalValue]:
        return self.__globals

    @property
    def modified(self) -> bool:
        for v in self.values:
            if v.modified:
                return True
        return False

    def __str__(self):
        return str(self.__globals)

    def __repr__(self):
        return str(self)

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise ValueError('Key must be integer')

        return next((g for g in self.__globals if g['idx'] == key), False)

    def __len__(self) -> int:
        return len(self.__globals)
    
    def to_json(self) -> dict:
        return {
            'globals': [v.to_json() for v in self.__globals]
        }

    @staticmethod
    def from_json_list(_json : List[dict]) -> Globals:
        vals = []
        for obj in _json:
            vals.append(GlobalValue.from_json(obj))
        return Globals(vals)

