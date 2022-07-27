from __future__ import annotations
from typing import Union, Dict, Tuple, Any

import os
from pathlib import PurePath
import re
import logging
import shutil

from utils import dbgprint, errprint
from utils import wasm_sourcemaps

SectionDetails = Dict[str, Dict[str, Union[str, int]]]
ModuleDetails = Dict[str, str]
DBGInfo = Tuple[SectionDetails, ModuleDetails]

# TODO
# 1. use wasmtime to generate usefull compact information about header, types and funbctions
# 2. use wat2wasm -v to generate all related functions body information
def generate_dbginfo(
    path: Union[PurePath, str], out: Union[PurePath, str, None]
) -> DBGInfo:
    """
    `file` is expected to point towards content produced by wasm-objdump v1.0.13 tool with headers flag
        e.g >> `wasm-objdump code.wat -h`
    """
    filepath = PurePath(path) if isinstance(path, str) else path
    ext = filepath.suffix
    if ext == "" or ext not in [".wat", ".wast"]:
        raise ValueError("`wat` or `wast` file expected")

    fname = filepath.name.split(".")[0]  # remove extension
    # dbgprint(f'GOT PATH ext {ext} name {filepath.name} -> {path}')

    outDirectory = out
    if out is None:
        outDirectory = PurePath("temporary/")
    elif isinstance(out, str):
        outDirectory = PurePath(out)
    else:
        outDirectory = out

    headers_path = outDirectory.joinpath(fname + ".dbg.headers")
    details_path = outDirectory.joinpath(fname + ".dbg.details")
    srcmap_path = outDirectory.joinpath(fname + ".dbg.verbose.txt")

    # dbgprint(f"""file name {fname}
    #             headers_path {headers_path}
    #             details_path {details_path}
    #             source maps path {srcmap_path}
    #         #   """)

    wasm_sourcemaps(filepath, outDirectory)

    sec = load_sections_info(headers_path)
    mod = load_module_details(details_path)
    mod["codes"] = read_sourcemap(srcmap_path)

    sec["no_extension_filename"] = fname
    if out is None:
        shutil.rmtree(outDirectory)

    return (sec, mod)


def load_sections_info(file: Union[PurePath, str]) -> SectionDetails:
    """
    `file` is expected to point towards content produced by wasm-objdump v1.0.13 tool with details flag
        e.g >> `wasm-objdump code.wat -x`
    """
    with open(file, "r") as headers:
        info = {}
        while "Sections:" not in headers.readline():
            pass

        for line in headers.readlines():
            words = line.split()
            if len(words) == 0:
                # skip blank line
                continue
            kind = words[0].lower()
            _, start = words[1].split("=")
            _, end = words[2].split("=")

            vals = {
                "start": int(start, 16),
                "end": int(end, 16),
                "size": int(end, 16) - int(start, 16),
            }
            if kind == "custom":
                vals["name"] = words[4]
            else:
                vals["count"] = int(words[-1])

            info[kind] = vals
        return info


def load_module_details(file: Union[PurePath, str]) -> ModuleDetails:
    parsers = {
        "Type": read_types,
        "Function": read_functions,
        "Export": read_export,
        "Code": read_code,
        "Import": read_import,
        "Custom": read_custom,
        "Table": read_tbl,
        "Memory": read_memory,
        "Elem": read_elem,
        "Global": read_globals,
    }
    mod = {}
    with open(file, "r") as details:
        while "Details:" not in details.readline():
            pass

        line = details.readline()
        while line:

            if len(line) == 0 or line == "\n":
                # skip blank line
                line = details.readline()
                continue

            kind = next((k for k in list(parsers) if k in line), None)

            assert kind is not None, f"issue parsing line {line}"

            if kind == "Custom":
                lines = details.readlines()
                p = parsers[kind]
                p(mod, lines)
                break

            quantity_str = "".join(re.findall(r"\d+", line))
            quantity = int(quantity_str)

            lines = [details.readline() for _ in range(quantity)]
            if kind == "Elem":
                seg_line = lines[0]
                seg_line = seg_line.split("count=")[1]
                elems_quantity = int(seg_line.split(" ")[0])
                for _ in range(elems_quantity):
                    lines.append(details.readline())

            parser = parsers[kind]
            parser(mod, lines)
            line = details.readline()

    return mod


def read_sourcemap(file: Union[PurePath, str]) -> Any:
    sourcemaps = {}
    with open(file, "r") as sources:
        line = sources.readline()
        section = 'section "Code" (10)'
        while section not in line:
            line = sources.readline()

        function = "function body "
        function_end = "FIXUP func body size"

        line = sources.readline()
        while line:
            while line and function not in line:
                line = sources.readline()

            if not line:
                break

            func_parts = line.split()
            func_idx = int(func_parts[-1])
            srcline_prefix = "@"
            end_inst = "; end"
            else_inst = "; else"
            src = []
            line_numbers = []

            line = sources.readline()
            while not (function_end in line):
                while (
                    not (srcline_prefix in line)
                    and not (function_end in line)
                    and not (end_inst in line)
                    and not (else_inst in line)
                ):
                    line = sources.readline()
                if function_end in line:
                    break

                instr = {}
                instr_line = line
                if srcline_prefix in line:
                    line_info = {}
                    line_parts = line[4:-3].split(",")
                    for l in line_parts:
                        k, v = l.split(":")
                        line_info[k.strip()] = int(v)
                    line_numbers.append(line_info)
                    instr_line = sources.readline()

                addr_part, inst_part = instr_line.split(";")
                instr_addr = addr_part.split(":")[0].split(" ")[-1]

                instr["addr"] = int("0x" + instr_addr, 16)
                instr["type"] = inst_part.strip()
                if len(line_numbers) > 0:
                    for k, v in line_numbers[-1].items():
                        instr[k] = v

                src.append(instr)
                line = sources.readline()

            sourcemaps[func_idx] = src
            line = sources.readline()

    return sourcemaps


def read_types(container, lines) -> None:
    types = []
    for type_line in lines:
        # line of the form '- type[2] (i32, f64)  -> i32'
        words = type_line.split()

        assert len(words) >= 5, f"incorrect quantity found: expected 5 got {len(words)}"

        type_idx = "".join(re.findall(r"\d+", words[1]))
        assert type_idx.isdigit()
        type_idx = int(type_idx)

        # str of the form (i32, f64) -> i32
        signature_str = "".join(words[2:])
        params_str, results_str = signature_str.split("->")

        # remove () and transform to  list of types [i32, f64]
        params = [] if params_str == "()" else params_str[1:-1].split(",")
        results = results_str if results_str != "nil" else None

        types.append({"params": params, "results": results, "idx": type_idx})

    container["types"] = types


def read_functions(container, lines):
    # Function[3]:
    #  - func[0] sig=0 <dummy>
    #  - func[1] sig=2 <fac>
    #  - func[2] sig=1 <fac5>
    funcs = container.get("funcs", [])
    for fun_line in lines:
        funcs.append(parse_function(fun_line))
    container["funcs"] = funcs


def read_export(container, lines):
    # Export[1]:
    #  - func[2] <fac5> -> "main"
    exps = {}
    for line in lines:
        words = line.split()
        func_idx_str = "".join(re.findall(r"\d+", words[1]))
        fun_idx = int(func_idx_str)
        export_name = words[-1]
        # remove quotes
        export_name = export_name[1:-1]
        exps[fun_idx] = export_name

    container["exports"] = exps


def read_import(container, lines):
    # Import[3]:
    #  - func[0] sig=0 <delay> <- env.chip_delay
    #  - func[1] sig=2 <getCTemp> <- env.sht3x_ctemp
    #  - func[2] sig=3 <sendTemp> <- env.write_f32
    funcs = container.get("funcs", [])

    for fun_line in lines:
        funcs.append(parse_function(fun_line))

    container["funcs"] = funcs
    container["imports"] = len(lines)


def read_code(container, lines):
    sizes = {}
    for line in lines:
        words = line.split()
        func_idx_str = "".join(re.findall(r"\d+", words[1]))
        fun_idx = int(func_idx_str)

        _, size_str = words[2].split("=")
        size = int(size_str)
        sizes[fun_idx] = size

    container["code_sizes"] = sizes


def read_custom(container, lines):
    _locals = {}
    for l in lines:
        if not "local" in l:
            continue
        _, fun_part, loc_part, name_part = l.split()
        fun_part = fun_part.split("[")[1]
        fun_part = fun_part[:-1]
        func_idx = int(fun_part)

        loc_part = loc_part.split("[")[1]
        loc_part = loc_part[:-1]
        local_idx = int(loc_part)

        # remove '<' and '>'
        local_name = name_part[1:-1]

        lst = _locals.get(func_idx, [])
        lst.append({"idx": local_idx, "name": local_name})
        _locals[func_idx] = lst

    container["locals"] = _locals


def read_globals(container, lines):
    _globals = []
    for line in lines:
        words = line.split()

        id_part = words[1]
        type_part = words[2]
        mutable_part = words[3]

        global_id = id_part.split("[")[1]
        global_id = int(global_id[:-1])

        global_type = type_part

        mutable = int(mutable_part.split("=")[1])
        mutable = mutable == 1

        _global = {"id": global_id, "type": global_type, "mutable": mutable}
        _globals.append(_global)

    container["globals"] = _globals


def parse_function(fun_line: str) -> Dict[str, Union[int, str]]:
    #  fun_line = 'func[0] sig=0 <dummy>'
    # or
    #  fun_line = 'func[0] sig=0 <delay> <- env.chip_delay'
    words = fun_line.split()
    assert len(words) >= 4, f"func definition incorrect format. Got {words}"
    func_idx_str = "".join(re.findall(r"\d+", words[1]))
    func_idx = int(func_idx_str)
    sign_idx_str = words[2].split("=")[1]
    sign_idx = int(sign_idx_str)

    func_name = words[3]

    # remove '<' '>'chars
    func_name = func_name[1:-1]
    f_obj = {"name": func_name, "idx": func_idx, "signature": sign_idx}
    if len(words) > 4:
        # fun_line = 'func[0] sig=0 <delay> <- env.chip_delay'
        import_name = words[5]
        f_obj["import_name"] = import_name
    return f_obj


def read_tbl(container, lines):
    # Table[1]:
    #  - table[0] type=funcref initial=5 max=5
    pass


def read_memory(container, lines):
    # Memory[1]:
    #  - memory[0] pages: initial=2
    pass


def read_elem(container, lines):
    # Elem[1]:
    #  - segment[0] flags=0 table=0 count=5 - init i32=0
    #   - elem[0] = func[5] <main>
    #   - elem[1] = func[3] <ff64tov>
    #   - elem[2] = func[2] <fi64tov>
    #   - elem[3] = func[1] <ff32tov>
    #   - elem[4] = func[0] <fi32tov>
    pass
