from __future__ import annotations
from typing import Union

import os
from pathlib import PurePath
import shutil

# TODO security!!!!!

WABT_BUILD = "c_libs/wabt/build/"


def wat2wasm(
    file: Union[str, PurePath],
    out_filename: Union[str, PurePath],
    des: Union[str, PurePath, None] = "",
) -> Union[bytes, None]:

    srcfile = PurePath(file) if isinstance(file, str) else file

    destDirectory = None
    if des is None:
        destDirectory = PurePath("tmp_build/")
    elif isinstance(des, str):
        destDirectory = PurePath(des) if des != "" else ""
    else:
        destDirectory = des

    out_filename = (
        PurePath(out_filename + ".wasm")
        if isinstance(out_filename, str)
        else out_filename
    )
    if destDirectory != "":
        out_filename = destDirectory.joinpath(out_filename)

    _make_parentsdir(out_filename)

    cmd = f"wat2wasm {srcfile} -o {out_filename}"
    if os.system(cmd) != 0:
        print("something wrong")
    else:
        _bytes = b""
        with open(out_filename, "rb") as _iobuff:
            _bytes = _iobuff.read()
        if des is None:
            shutil.rmtree(destDirectory)
        return _bytes


def wasm_sourcemaps(src: PurePath, out: PurePath) -> None:
    from subprocess import run, PIPE

    global WABT_BUILD
    no_ext_name = src.name.split(".")[0]
    wasm_path = out.joinpath(no_ext_name + ".dbg.wasm")
    headers_path = out.joinpath(no_ext_name + ".dbg.headers")
    details_path = out.joinpath(no_ext_name + ".dbg.details")
    srcmap_path = out.joinpath(no_ext_name + ".dbg.verbose.txt")

    # make directory if needed first
    _make_parentsdir(wasm_path)
    comp2wasm = [f"{WABT_BUILD}./wat2wasm", "--debug-names", "-v", src, "-o", wasm_path]
    p = run(comp2wasm, stdout=PIPE, stderr=PIPE)
    with open(srcmap_path, "w") as srcmap_file:
        srcmap_file.write(p.stdout.decode())

    wasm2headers = f"{WABT_BUILD}./wasm-objdump {wasm_path} -h > {headers_path}"
    if os.system(wasm2headers) != 0:
        print(f"error in {wasm2headers}")
        return

    wasm2details = f"{WABT_BUILD}./wasm-objdump {wasm_path} -x > {details_path}"
    if os.system(wasm2details) != 0:
        print(f"error in {wasm2details}")
        return


def _make_parentsdir(p: PurePath):
    # make output dir if needed
    if not os.path.exists(os.path.dirname(p)):
        try:
            os.makedirs(os.path.dirname(p))
        except OSError as exc:
            print(exc)
            raise
