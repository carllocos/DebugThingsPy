from __future__ import annotations
from typing import Union, List, Any

from utils import dbgprint, errprint
from web_assembly import ConstValue

ValType = Union[float, int]


class GlobalValue(ConstValue):
    def __init__(
        self, type_str: str, val: ValType, mutable: bool = False
    ) -> GlobalValue:
        super().__init__(type_str, val)
        self.__mutable = mutable
        self.__original = None
        self.__idx = None

    @property
    def idx(self) -> Union[None, int]:
        return self.__idx

    @idx.setter
    def idx(self, i: int) -> None:
        self.__idx = i

    @property
    def mutable(self) -> bool:
        return self.__mutable

    @property
    def original(self) -> Union[None, GlobalValue]:
        return self.__original

    @property
    def modified(self) -> bool:
        return self.__original is not None

    def _set_value(self, v: ValType) -> None:
        # TODO correct
        if self.__original is None:
            self.__original = self.copy()

        return v

    def __repr__(self) -> str:
        ids = "" if self.idx is None else f"idx={self.idx}, "
        return f"GlobalValue({ids}value={self.value}, type={self.type})"

    def get_latest(self) -> GlobalValue:
        gv = self.copy()
        if not self.modified:
            return gv

        self.value = self.__original.value
        self.__original = None
        return gv

    def copy(self) -> GlobalValue:
        gv = GlobalValue(self.type, self.value, self.mutable)
        gv.idx = self.idx
        return gv

    def to_json(self) -> dict:
        j = {"type": self.type, "value": self.value}
        if self.idx is not None:
            j["idx"] = self.idx
        j["mutable"] = self.mutable if self.mutable is None else True
        return j

    @staticmethod
    def from_json(_json: dict) -> GlobalValue:
        gv = GlobalValue(_json["type"], _json["value"])
        if _json.get("idx", None) is not None:
            gv.idx = _json["idx"]
        return gv


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
            raise ValueError("Key must be integer")
        found = next((g for g in self.values if g.idx == key), None)
        if found is None:
            return self.values[key]
        return found

    def __len__(self) -> int:
        return len(self.__globals)

    def get_update(self, module: Any) -> Union[None, Globals]:
        _values = []
        for v in self.values:
            if v.modified:
                if not valid_value(v):
                    raise ValueError(f"invalid value set for global value {v.type}")
            _values.append(v.get_latest())
        return Globals(_values)

    def copy(self) -> Globals:
        _vals = [v.copy() for v in self.values]
        return Globals(_vals)

    def to_json(self) -> dict:
        return {"globals": [v.to_json() for v in self.__globals]}

    @staticmethod
    def from_json_list(_json: List[dict]) -> Globals:
        vals = []
        for idx, obj in enumerate(_json):
            obj["idx"] = idx
            vals.append(GlobalValue.from_json(obj))
        return Globals(vals)


def valid_value(v: GlobalValue) -> bool:
    return True

