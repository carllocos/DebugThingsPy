from __future__ import annotations
from typing import Union, Dict
from pathlib import PurePath
import logging

from utils import wat2wasm
from web_assembly import Functions, Types, Type, Codes, Expr
from web_assembly import generate_dbginfo, load_module_details, DBGInfo


logging.basicConfig(level=logging.DEBUG)

def dbgprint(s):
    logging.debug(s)


class WAModule:
    def __init__(self: WAModule, types: Types, funcs: Functions, codes: Codes) -> WAModule:
        super().__init__()
        self.__types = types
        self.__funcs = funcs
        self.__codes = codes
        self.__table = []
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
    def build_out(self, _buildout) -> None:
        self.__buildout = _buildout

    def linenr(self, nr: int):
        return self.codes.linenr(nr)

    def addr(self, addr: Union[str, int]) -> Union[Expr, None]:
        return self.codes.addr(addr)

    # def copy(self) -> WAModule:
    #     _codes = self.codes.copy()
    #     _types = self.types.copy()
    #     _funcs = self.functions.copy()
    #     m = WAModule(_types, _funcs, _codes)
    #     m.filepath = self.filepath
    #     m.no_extension_filename = self.no_extension_filename
    #     m.build_out = self.build_out
    #     return m

    def compile(self) -> bytes:
        fp = self.filepath
        fn = self.no_extension_filename
        out = self.build_out
        _bytes = wat2wasm(fp, fn, out)
        return _bytes

    @classmethod
    def from_file(cls, path: str, out: Union[str, None] = None) -> WAModule:
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
        return csl(types, funcs, codes)

