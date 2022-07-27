from __future__ import annotations
from typing import List, Union, Dict
from pathlib import PurePath
import logging

from utils import wat2wasm
from utils import get_logger
from web_assembly import Function, Functions, Types, Type, Codes, Expr
from web_assembly import generate_dbginfo, load_module_details, DBGInfo

WA_logger = get_logger("WAModule")


class WAModule:
    def __init__(self: WAModule, types: Types, funcs: Functions, codes: Codes):
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
        self.__cached_wasm = None

    @property
    def types(self) -> Types:
        return self.__types

    @property
    def functions(self) -> Functions:
        return self.__funcs

    @property
    def exports(self) -> List[Function]:
        return self.__funcs.exports

    @property
    def imports(self) -> List[Function]:
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
        self.__no_extension_filename = fn

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

    ##TODO remove
    def make_proxy_config(self, functions_2_proxy: List[Union[str, int]]) -> Dict:
        fun_ids = []
        for fun in functions_2_proxy:
            cleaned_name = fun
            ##TODO cleanup
            if isinstance(fun, str) and fun[0] == "$":
                cleaned_name = fun[1:]
            f = self.functions[cleaned_name]
            if f is None:
                raise ValueError(
                    f"Proxy error: proxy function `{fun}` is not declared in module"
                )
            fun_ids.append(f.idx)
        return fun_ids

    # def copy(self) -> WAModule:
    #     _codes = self.codes.copy()
    #     _types = self.types.copy()
    #     _funcs = self.functions.copy()
    #     m = WAModule(_types, _funcs, _codes)
    #     m.filepath = self.filepath
    #     m.no_extension_filename = self.no_extension_filename
    #     m.build_out = self.build_out
    #     return m

    def is_compiled(self) -> bool:
        return self.__cached_wasm is not None

    def get_cache(self) -> bytes:
        return self.__cached_wasm

    def compile(self, cache: bool = False) -> bytes:
        WA_logger.info("Compiling module")
        if self.is_compiled():
            WA_logger.info("Using cached Wasm")
            return self.get_cache()
        fp = self.filepath
        fn = self.no_extension_filename
        out = self.build_out
        _bytes = wat2wasm(fp, fn, out)
        if cache:
            WA_logger.info(f"Caching Wasm")
            self.__cached_wasm = _bytes
        return _bytes

    @staticmethod
    def from_file(path: str, out: Union[str, None] = None) -> WAModule:
        dbg_info = generate_dbginfo(path, out)
        wm = WAModule.from_dbginfo(dbg_info)
        wm.filepath = path
        s, _ = dbg_info
        wm.no_extension_filename = s["no_extension_filename"]
        wm.build_out = out

        return wm

    @staticmethod
    def from_dbginfo(dbg_info: DBGInfo) -> WAModule:
        types = Types.from_dbg(dbg_info)
        codes = Codes.from_dbg(dbg_info)
        funcs = Functions.from_dbg(dbg_info, codes, types)
        return WAModule(types, funcs, codes)
