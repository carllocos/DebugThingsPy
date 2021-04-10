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
        self.__filepath = None
        self.__no_extension_filename = None
        self.__buildout = None

    @property
    def types(self) -> Types:
        return self.__types

    @property
    def functions(self) -> Functions:
        return self.__funcs

    @property
    def exports(self) -> Functions:
        return self.__funcs.exports

    @property
    def imports(self) -> Functions:
        return self.__funcs.imports

    @property
    def codes(self) -> Codes:
        return self.__codes

    @property
    def filepath(self) -> Union[str, None]:
        return self.__filepath

    @filepath.setter
    def filepath(self, fp: str) -> None:
        self.__filepath = fp

    @property
    def no_extension_filename(self) -> Union[str, None]:
        return self.__no_extension_filename 

    @no_extension_filename.setter
    def no_extension_filename(self, fn) -> None:
        self.__no_extension_filename  = fn

    @property
    def build_out(self) -> Union[str, None]:
        return self.__buildout

    @build_out.setter
    def build_out(self, bo) -> None:
        self.__buildout = bo

    @classmethod
    def from_file(cls, path: str, out: str) -> WAModule:
        dbg_info = generate_dbginfo(path, out)
        wm = WAModule.from_dbginfo(dbg_info)
        wm.filepath = path
        s, _ = dbg_info
        wm.no_extension_filename = s['no_extension_filename']
        wm.build_out = out

        return wm

    @classmethod
    def from_dbginfo(csl, dbg_info: DBGInfo) -> WAModule:
        types = Types.from_dbg(dbg_info)
        codes = Codes.from_dbg(dbg_info)
        funcs = Functions.from_dbg(dbg_info, codes, types)
        dbgprint(f'The exports {funcs.exports}')
        return csl(types, funcs, codes)

    # @classmethod
    # def test(cls):
    #     return cls.from_file("../examples/fac_case/fac.wat")


def dbgprint(s):
    logging.debug(s)
