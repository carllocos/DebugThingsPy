from __future__ import annotations
from typing import Union, List

from abc import ABC, abstractmethod
from interfaces import AMessage

class AMedium(ABC):


    @abstractmethod
    def start_connection(self, dev):
        raise NotImplementedError

    @abstractmethod
    def send(self, msg: Union[AMessage, List[AMessage]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def close_connection(self, dev):
        raise NotImplementedError