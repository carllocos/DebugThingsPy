from __future__ import annotations
from typing import Union
from things import DebugSession

from utils import wat2wasm
from web_assembly import WAModule 

class ChangesHandler:

    def __init__(self, wamodule: WAModule) -> ChangesHandler:
        self.__mod = wamodule
        self.__sessions = []

    @property
    def session(self) -> Union[DebugSession, None]:
        if self.__sessions:
            return self.__sessions[-1]

    @property
    def modified(self) -> bool:
        return self.__sessions and self.session.modified 

    @property
    def module(self) ->  WAModule:
        return self.__mod

    def version(self, v: int)-> Union[DebugSession, None]:
        """
        version starts at 0, being the intial Sessionversion.
        version 1 is the Sessionversion obtained after a first change
        """
        if len(self.__sessions) == 0:
            return None
        return self.__sessions[v]

    def add(self, s: DebugSession) -> None:
        s.version = len(self.__sessions)
        self.__sessions.append(s)

    #FIXME temporary returns bytes
    def commit(self) -> bytes:
        fp = self.module.filepath
        fn = self.module.no_extension_filename + '_version' + str(self.version)
        out = self.module.build_out
        _bytes = wat2wasm(fp, fn, '' if out is None else out)
        return _bytes