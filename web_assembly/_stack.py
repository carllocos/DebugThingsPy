from __future__ import annotations
from typing import Any, Union, List
from dataclasses import dataclass, field

from utils import dbgprint, errprint
from web_assembly import ConstValue


class StackValue(ConstValue):
    def __init__(self, _type: str, val: Any, idx: int, name: Union[str, None] = None):
        super().__init__(_type, val)
        self.__idx = idx
        self.__stack = None
        self.__original = None
        self.__name = name

    @property
    def name(self) -> Union[str, None]:
        return self.__name

    @name.setter
    def name(self, n: str) -> None:
        self.__name = n

    @property
    def original(self) -> Any:
        return self.__original

    @original.setter
    def original(self, org: Any) -> None:
        self.__original = org

    @property
    def idx(self) -> int:
        return self.__idx

    @property
    def stack(self) -> Union[Stack, None]:
        return self.__stack

    @stack.setter
    def stack(self, s: Stack) -> None:
        self.__stack = s

    def _set_value(self, v) -> None:
        if self.type in ["f32", "f64"]:
            if not isinstance(v, float):
                raise ValueError(f"exptected a value of type '{self.type}'")
        else:
            if not isinstance(v, int):
                raise ValueError(f"exptected a value of type '{self.type}'")

        if self.__original is None:
            self.__original = self.copy()
            self.__original.stack = self.stack
        return v

    def __str__(self) -> str:
        return f"{self.idx}: {self.type}.const  {self.value}"

    def __repr__(self) -> str:
        end = ")"
        if self.name is not None:
            end = f", name={self.name})"
        return f"StackValue(idx={self.idx}, value={self.value}, type={self.type}{end}"

    @property
    def modified(self) -> bool:
        return self.__original is not None

    def get_latest(self) -> StackValue:
        v = self.copy()
        if not self.modified:
            return v

        self.value = self.__original.value
        self.__original = None
        return v

    def copy(self) -> StackValue:
        return StackValue(self.type, self.value, self.idx, self.name)

    def to_json(self) -> dict:
        v = {"type": self.type, "value": self.value, "idx": self.idx}
        if self.name is not None:
            v["name"] = self.name
        return v

    @staticmethod
    def from_const(const: ConstValue, idx: int) -> StackValue:
        return StackValue(const.type, const.val, idx)

    @staticmethod
    def from_json(_json: dict) -> StackValue:
        return StackValue(_json["type"], _json["value"], _json["idx"])


class Stack:
    def __init__(self):
        self.__values = []
        self.__idx = None
        self.__values.sort(key=lambda sv: sv.idx, reverse=True)

    @property
    def values(self) -> List[StackValue]:
        return self.__values

    def add(self, type_str: str, val: Any, idx: int) -> None:
        sv = StackValue(type_str, val, idx)
        sv.stack = self
        self.__values.append(sv)

    def __getitem__(self, key: Any) -> StackValue:
        return self.__values[key]

    def __add__(self, e: Any) -> Stack:
        if not isinstance(e, StackValue):
            raise ValueError("stackValue expected")
        self.__values.append(e)
        return self

    @property
    def modified(self) -> bool:
        for v in self.__values:
            if v.modified:
                return True
        return False

    def get_update(self, mod: Any) -> Union[None, Stack]:
        if not self.modified:
            return None

        s = Stack()
        for v in self.__values:
            s += v.get_latest()

        return s

    def __len__(self) -> int:
        return len(self.values)

    def reset_iterator(self):
        self.__idx = 0

    def print(self):
        s = ""
        for v in self.__values:
            s = f"StackValue(idx={v.idx},type={v.type},val={v.value})" + "\n" + s
        print(s)

    def copy(self) -> Stack:
        s = Stack()
        for v in self.values:
            s += v.copy()
        return s

    def to_json(self) -> dict:
        return {"stack": [sv.to_json() for sv in self.values]}

    @staticmethod
    def from_json_list(_json: List[dict]) -> Stack:
        stack = Stack()
        for idx, val_obj in enumerate(_json):
            val_obj["idx"] = idx
            stack += StackValue.from_json(val_obj)
        return stack
