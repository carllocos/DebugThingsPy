from __future__ import annotations
from typing import Union
from things import SessionVersion

from utils import wat2wasm
from web_assembly import WAModule 

class ChangesHandler:

    def __init__(self, wamodule: WAModule) -> ChangesHandler:
        self.__session = None
        self.__mod = wamodule
        self.__changes = []

    @property
    def session(self) -> Union[SessionVersion, None]:
        return self.__session

    @property
    def module(self) ->  WAModule:
        return self.__mod

    @property
    def version(self) -> int:
        return len(self.__changes)

    def get_change(self, version: int) -> Union[SessionVersion, None]:
        """
        version starts at 0, being the intial Sessionversion.
        version 1 is the Sessionversion obtained after a first change
        """
        if version == 0:
            return self.session
        return self.__changes[version - 1]

    #FIXME temporary returns bytes
    def commit(self) -> bytes:
        fp = self.module.filepath
        fn = self.module.no_extension_filename + '_version' + str(self.version)
        out = self.module.build_out
        _bytes = wat2wasm(fp, fn, '' if out is None else out)
        return _bytes

    def change(self, nd: SessionVersion) -> None:
        if self.session is None:
            self.__session = nd
        else:
            self.__changes.append(nd)

    # def commit_test(self):
    #     file_path =  'examples/fac_case/fac.wasm'
    #     with open(file_path, 'r') as f:
    #             array_name = file_path.replace('/','_').replace('.','_')
    #             output = "unsigned char %s[] = {" % array_name
    #             length = 0
    #             while True:
    #                 buf = f.read(12)

    #                 if not buf:
    #                     output = output[:-2]
    #                     break
    #                 else:
    #                     output += "\n  "

    #                 for i in buf:
    #                     output += "0x%02x, " % ord(i)
    #                     length += 1
    #             output += "\n};\n"
    #             output += "unsigned int %s_len = %d;" % (array_name, length)
    #             print(output)


    # def commit_test2(self) -> None:
                # assert w.hex() == the_bytes.hex(), f'{w.hex()} == {the_bytes.hex()}'
    # def commit_test2(self):
    #     import codecs
    #     with open('examples/fac_case/fac.wasm', 'rb') as f:
    #         print(f.read())
    #         for chunk in iter(lambda: f.read(32), b''):
    #             print(codecs.encode(chunk, 'hex'))