from __future__ import annotations
from typing import Union, List, Any
from web_assembly import SectionDetails, ModuleDetails, DBGInfo, Codes, Code,Type, Types

#TODO distinguish between types declared and types defined when function defined. Make abstraction over type signature in Type

class Function:
    def __init__(self,
                idx: int,
                signature: Type,
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
    def signature(self) -> Type:
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
            return self.__str2funcs.get(key, None)
        else:
            return self.__int2funcs.get(key, None)

    @property
    def exports(self) -> List[Function]:
       return list(filter(lambda f: f.export_name is not None, self.__int2funcs.values()))

    @property
    def imports(self) -> List[Function]:
       return list(filter(lambda f: f.import_name is not None, self.__int2funcs.values()))

    @staticmethod
    def from_dbg(dbg_info: DBGInfo, codes: Codes, types: Types ):
        sec : SectionDetails = dbg_info[0]
        mod : ModuleDetails = dbg_info[1]

        # imports = mod['imports']
        # code = mod['code']
        exports = mod['exports']
        imports = {}
        funcs = []
        for f in mod['funcs']:

            #TODO take into acount lack of type declaration 
            sign = f['signature']
            if isinstance(sign, int):
                sign = types[sign]
            else:
                sign = Type(sign, [], [], None)
                
            idx = f['idx']
            name = f.get('name', None)
            export_name = exports.get(idx, None)
            import_name = imports.get(idx, None)
            code = codes[idx]

            funcs.append(Function(idx, sign, name, export_name, import_name, code))

        func_header = sec['function']
        return Functions(funcs, func_header['start'], func_header['end'])
