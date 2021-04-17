from __future__ import annotations
from typing import Union, List, Any

class Memory:
    def __init__(self, _min: int, _max: Union[int, None], pages: int, byts: bytes):
        self.__min = _min
        self.__max = _max
        self.__pages = pages
        self.__bytes = byts

    @property
    def bytes(self)-> bytes:
        return self.__bytes

    @property
    def min(self) -> int:
        return self.__min

    @property
    def max(self) -> Union[int, None]:
        return self.__max

    @property
    def pages(self):
        return self.__pages

    @property
    def modified(self)-> bool:
        return False

    def get_update(self) -> Union[None, Memory]:
        return None

    def __repr__(self):
        return f'Memory(min={self.min}, max={self.max}, pages={self.pages},bytes={self.bytes})'

    def to_json(self) -> dict:
        _json = {
            'min': self.min,
            'bytes': self.bytes,
            'pages': self.pages
        }
        if self.max is not None:
            _json['max'] = self.max
        return _json

    @staticmethod
    def from_json(_json: dict) -> Memory:
        return Memory(_json['min'], _json.get('max', None), _json['pages'], _json['bytes'])

class Memories:

    def __init__(self, memories: List[Memory])  -> Memories:
        self.__mems = memories

    @property
    def memories(self) -> List[Memory]:
        return self.__mems

    def __getitem__(self, key: Any) -> Memory:
        if not isinstance(key, int):
            raise ValueError(f'key error')
        return self.__mems[key]