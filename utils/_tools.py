from __future__ import annotations
from typing import Union

import os
from pathlib import PurePath

#TODO security!!!!!
def wat2wasm(file: Union[str, PurePath], out: Union[str, PurePath], des: Union[str, PurePath] = '') -> bytes:

    srcfile = PurePath(file) if isinstance(file, str) else file

    if des != '':
        des = PurePath(des) if isinstance(des, str) else des
    out = PurePath(out + '.wasm') if isinstance(out, str) else out
    outfile = out
    if des != '':
        outfile = des.joinpath(out)

    _make_parentsdir(outfile)

    cmd = f'wat2wasm {srcfile} -o {outfile}'
    retcode = os.system(cmd)
    if retcode != 0:
        print("something wrong")
    else:
        with open(outfile, 'rb') as _iobuff:
            _bytes = _iobuff.read()
            # print(_bytes.hex())
            # print(f'the lenght {len(_bytes)}')
            return _bytes


def wasm_sourcemaps(src: PurePath, out: PurePath) -> None:
    no_ext_name = src.name.split('.')[0]
    wasm_path = out.joinpath(no_ext_name + '.dbg.wasm')
    headers_path = out.joinpath(no_ext_name + '.dbg.headers')
    details_path = out.joinpath(no_ext_name + '.dbg.details')
    srcmap_path = out.joinpath(no_ext_name +  '.dbg.verbose.txt')

    #make directory if needed first
    _make_parentsdir(wasm_path)
    comp2wasm  = f'c_libs/wabt/build/./wat2wasm --debug-names -v {src} -o {wasm_path} > {srcmap_path}'
    if os.system(comp2wasm) != 0:
        print(f'error in {comp2wasm}')
        return

    wasm2headers = f'wasm-objdump {wasm_path} -h > {headers_path}'
    if os.system(wasm2headers) != 0:
        print(f'error in {wasm2headers}')
        return

    wasm2details = f'wasm-objdump {wasm_path} -x > {details_path}'
    if os.system(wasm2details) != 0:
        print(f'error in {wasm2details}')
        return

def _make_parentsdir(p: PurePath):
    #make output dir if needed
    if not os.path.exists(os.path.dirname(p)):
        try:
            os.makedirs(os.path.dirname(p))
        except OSError as exc:
            print(exc)
            raise