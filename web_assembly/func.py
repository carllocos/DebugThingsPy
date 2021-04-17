from __future__ import annotations
from typing import Union, List, Any
from dataclasses import dataclass

from web_assembly import SectionDetails, ModuleDetails, DBGInfo, Codes, Code,Type, Types

#TODO distinguish between types declared and types defined when function defined. Make abstraction over type signature in Type

@dataclass
class Local:
    idx: int
    name: Union[str, None]

@dataclass
class Function:
    idx: int
    signature: Type
    name: Union[str, None]
    export_name: Union[str, None]
    import_name: Union[str, None]
    locals: List[Local]
    code: Union[None, Code] = None
   
    def any_name(self) -> Union[str, None]:
        if self.name is not None:
            return self.name
        elif self.export_name is not None:
            return self.export_name
        else:
            return self.import_name

    def __str__(self):
        prefix = '<'
        if self.export_name is not None:
            prefix += 'exported '
        elif self.import_name is not None:
            prefix += 'imported '
        prefix += f'fun {self.idx}'
        return f'{prefix}: {self.any_name()} {str(self.signature)}>'

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

        self.__funcs = funcs
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

    def print(self):
        for f in self.__funcs:
            print(str(f))

    @staticmethod
    def from_dbg(dbg_info: DBGInfo, codes: Codes, types: Types ):
        sec : SectionDetails = dbg_info[0]
        mod : ModuleDetails = dbg_info[1]

        # imports = mod['imports']
        # code = mod['code']
        exports = mod['exports']
        imports = {}
        funcs = []
        _locals= mod.get('locals', {})
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
            _fun_locals = []
            for _loc in _locals.get(idx, []):
                _fun_locals.append(Local(_loc['idx'], _loc['name']))

            funcs.append(Function(idx, sign, name, export_name, import_name, _fun_locals, code))

        func_header = sec['function']
        return Functions(funcs, func_header['start'], func_header['end'])
