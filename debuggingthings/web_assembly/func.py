from __future__ import annotations
from typing import Union, List, Any
from web_assembly import SectionDetails, ModuleDetails, DBGInfo, Codes, Code

class Function:
    def __init__(self,
                idx: int,
                signature: int,
                name: Union[str, None],
                export_name: Union[str, None],
                import_name: Union[str, None],
                code: Union[None, Code] = None):
        self.__idx = idx
        self.__signature = signature
        self.__name = name
        self.__export = export_name
        self.__import = import_name
        self.__code = code

    @property
    def idx(self) -> int:
        return self.__idx

    @property
    def name(self) -> Union[str, None]:
        return self.__name
    
    @property
    def signature(self) -> int:
        return self.__signature

    @property
    def export_name(self) -> Union[str, bool]:
        return self.__export 

    @property
    def import_name(self) -> Union[str, bool]:
        return self.__import

    @property
    def code(self) -> Union[Code, None]:
        return self.__code

class Functions:
    def __init__(self, funcs: List[Function], start: int, end: int):
        #TODO start & end

        str2funcs, int2funcs = {}, {}
        for f in funcs:
            int2funcs[f.idx] = f
            if f.name is not None:
                str2funcs[f.name] = f
            
            if f.export_name is not None and f.export_name != f.name:
                str2funcs[f.export_name] = f

        self.__str2funcs = str2funcs
        self.__int2funcs = int2funcs
     
    def __getitem__(self, key: Any) -> Function:
        if isinstance(key, str):
            return self.__str2funcs[key]
        else:
            return self.__int2funcs[key]

    @property
    def exports(self) -> List[Function]:
       return list(filter(lambda f: f.export_name is not None, self.__int2funcs.values()))

    @property
    def imports(self) -> List[Function]:
       return list(filter(lambda f: f.import_name is not None, self.__int2funcs.values()))

    @staticmethod
    def from_dbg(dbg_info: DBGInfo, codes: Union[Codes, None] = None):
        sec : SectionDetails = dbg_info[0]
        mod : ModuleDetails = dbg_info[1]

        # imports = mod['imports']
        # code = mod['code']
        exports = mod['exports']
        imports = {}
        codes = {}
        funcs = []
        for f in mod['funcs']:
            sign = f['signature']
            idx = f['idx']
            name = f.get('name', None)
            export_name = exports.get(idx, None)
            import_name = imports.get(idx, None)
            code = codes.get(idx, None)
            funcs.append(Function(idx, sign, name, export_name, import_name, code))

        func_header = sec['function']
        return Functions(funcs, func_header['start'], func_header['end'])
