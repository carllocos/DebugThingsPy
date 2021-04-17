from __future__ import annotations
from typing import Any, Union

const_types = ['i32', 'i64', 'f32', 'f64']
ValType = Union[float, int]

class ConstValue:
    def __init__(self, _type: str, val: ValType) -> ConstValue:
        if _type not in const_types:
            raise ValueError(f'incorrect type for const')

        self.__type = _type
        self.__val = val

    @property
    def type(self) -> str:
        return self.__type

    @property
    def value(self) -> ValType:
        return self._get_value()

    def _get_value(self) -> ValType:
        return self.__val

    @value.setter
    def value(self, v: ValType) -> None:
        self._set_value(v)

    def _set_value(self, v: ValType) -> None:
        raise ValueError(f'changing value is unauthorized')