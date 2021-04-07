from __future__ import annotations
from typing import List, Union, Any
from web_assembly import DBGInfo, SectionDetails, ModuleDetails

Parameters = List[str]
Results = List[str]

class Type:
    def __init__(self, idx: int, params: Parameters, results: Results, name: Union[str, None]):
        self.__params = params
        self.__results = results
        self.__idx = idx
        self.__name = name

    @property
    def parameters(self) -> Parameters:
        return self.__params

    @property
    def results(self) -> Results:
        return self.__results

    @property
    def name(self) -> Union[str, None]:
        return self.__name
    
    @property
    def idx(self) -> int:
        return self.__idx

class Types:
    def __init__(self, types: List[Type], start: int, end: int):
        str2types, int2types = {}, {}
        for t in types:
            int2types[t.idx] = t
            if t.name is not None:
                str2types[t.name] = t

        self.__str2types = str2types
        self.__int2types = int2types
     
    def __getitem__(self, key: Any) -> Union[Type, None]:
        if isinstance(key, str):
            return self.__str2types.get(key, None)
        elif isinstance(key, int):
            return self.__int2types.get(key, None)
        else:
            raise ValueError("`key` must be an int or str")

    @staticmethod
    def from_dbg(dbg_info: DBGInfo):
        sec : SectionDetails = dbg_info[0]
        mod : ModuleDetails = dbg_info[1]
        types = []
        for type_signature in mod['types']:
            params = type_signature['params']
            res = type_signature['results']
            idx = type_signature['idx']
            name = type_signature.get('name', None)
            types.append(Type(idx, params, res, name))

        type_header = sec['type']
        return Types(types, type_header['start'], type_header['end'])
