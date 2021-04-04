from __future__ import annotations
from typing import Union, Dict
from pathlib import PurePath
import logging

from web_assembly import Functions, Tables, Globals, Memories, Types, Type, Codes
from web_assembly import generate_dbginfo, load_module_details, DBGInfo 


logging.basicConfig(level=logging.DEBUG)


class WAModule:
    def __init__(self: WAModule, types: Types, funcs: Functions, codes: Codes) -> WAModule:
        super().__init__()
        self.__types = types
        self.__funcs = funcs
        self.__codes = codes
        self.__tables = []
        self.__memories = []
        self.__globals = []

    @property
    def section_types(self) -> Types:
        return self.__types

    @property
    def section_functions(self) -> Functions:
        return self.__funcs

    @property
    def section_exports(self) -> Functions:
        return self.__funcs.exports

    @property
    def section_imports(self) -> Functions:
        return self.__funcs.imports

    @property
    def section_code(self) -> Codes:
        return self.__codes

    @classmethod
    def from_file(cls, path: str) -> WAModule:
        dbg_info = generate_dbginfo(path)
        return WAModule.from_dbginfo(dbg_info)

    @classmethod
    def from_dbginfo(csl, dbg_info: DBGInfo) -> WAModule:
        types = Types.from_dbg(dbg_info)
        codes = Codes.from_dbg(dbg_info)
        funcs = Functions.from_dbg(dbg_info)
        dbgprint(f'The exports {funcs.exports}')
        return  csl(types, funcs, codes)

def dbgprint(s):
    logging.debug(s)

