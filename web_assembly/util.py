from __future__ import annotations
from typing import Union, Dict, Tuple, Any

import os
from pathlib import PurePath
import re
import logging

from utils import wasm_sourcemaps

logging.basicConfig(level=logging.DEBUG)

SectionDetails = Dict[str, Dict[str, Union[str, int]]]
ModuleDetails = Dict[str, str]
DBGInfo = Tuple[SectionDetails, ModuleDetails]

def dbgprint(s):
    logging.debug(s)


def raise_error(m):
    raise ValueError(m)

#TODO 
# 1. use wasmtime to generate usefull compact information about header, types and funbctions
# 2. use wat2wasm -v to generate all related functions body information
def generate_dbginfo(path: Union[PurePath, str], out: Union[PurePath, str]) -> DBGInfo:
    """
    `file` is expected to point towards content produced by wasm-objdump v1.0.13 tool with headers flag
        e.g >> `wasm-objdump code.wat -h`
    """
    filepath = PurePath(path) if isinstance(path, str) else path
    ext = filepath.suffix
    if ext == '' or ext not in ['.wat', '.wast']:
        raise ValueError('`wat` or `wast` file expected')

    fname = filepath.name.split(".")[0]# remove extension 
    dbgprint(f'GOT PATH ext {ext} name {filepath.name} -> {path}')

    out = PurePath(out) if isinstance(out, str) else out

   

    # parent_path = "/".join(filepath.parts[:-1]) #TODO change name for generic sol
    # tmp_dir =  PurePath(parent_path) 

    headers_path = out.joinpath(fname + '.dbg.headers')
    details_path = out.joinpath(fname + '.dbg.details')
    srcmap_path = out.joinpath(fname +  '.dbg.verbose.txt')


    dbgprint(f"""file name {fname}
                headers_path {headers_path}
                details_path {details_path}
                source maps path {srcmap_path}
              """)


    # wasm_headers(filepath, headers_path)
    # wasm_details(filepath, details_path)
    wasm_sourcemaps(filepath, out)

    sec = load_sections_info(headers_path)
    mod = load_module_details(details_path)
    mod['codes'] = read_sourcemap(srcmap_path)

    sec['no_extension_filename'] = fname
    return (sec, mod)

def load_sections_info(file: Union[PurePath, str]) -> SectionDetails:
    """
    `file` is expected to point towards content produced by wasm-objdump v1.0.13 tool with details flag
        e.g >> `wasm-objdump code.wat -x`
    """
    with open(file, 'r') as headers:
        info = {}
        while 'Sections:' not in headers.readline():
            pass

        for line in headers.readlines():
            words = line.split()
            if len(words) == 0:
                #skip blank line
                continue
            kind = words[0].lower()
            _, start = words[1].split('=')
            _, end = words[2].split('=')

            vals = {
                'start' : int(start, 16),
                'end' :int(end, 16),
                'size' : int(end, 16) - int(start, 16) 
            }
            if kind == 'custom':
                vals['name'] = words[4] 
            else:
                vals['count'] = int(words[-1])

            info[kind] = vals
        return info

def load_module_details(file: Union[PurePath, str]) -> ModuleDetails:
    parsers = {
        'Type': read_types,
        'Function': read_functions,
        'Export': read_export,
        'Code': read_code,
        'Import': read_import,
        'Custom': read_custom,
        'Table': read_tbl,
        'Memory': read_memory,
        'Elem': read_elem
    }
    mod = {}
    with open(file, 'r') as details:
        while 'Details:' not in details.readline():
            pass

        line = details.readline()
        while line:

            if len(line) == 0 or line == '\n':
                #skip blank line
                line =  details.readline()
                continue

            kind = next((k for k in list(parsers) if k in line), None)
            if kind == 'Custom':
                break

            assert kind is not None, f'issue parsing line {line}'

            quantity_str = ''.join(re.findall(r'\d+', line))
            quantity = int(quantity_str)

            lines = [details.readline()  for _ in range(quantity)]
            if kind == 'Elem':
                seg_line = lines[0]
                seg_line = seg_line.split('count=')[1]
                elems_quantity = int(seg_line.split(' ')[0])
                for _ in range(elems_quantity):
                    lines.append(details.readline())

            parser = parsers[kind]
            parser(mod, lines)
            line =  details.readline()

    return mod

def read_sourcemap(file: Union[PurePath, str]) -> Any:
    dbgprint('reading sourcemaps')
    sourcemaps = {}
    with open(file, 'r') as sources:
        line = sources.readline()
        section = 'section "Code" (10)'
        while section not in line:
            line = sources.readline()

        dbgprint('starting first function')
        function = 'function body '
        function_end = 'FIXUP func body size'

        line = sources.readline()
        while line:
            while line and function not in line:
                line = sources.readline()

            if not line:
                break

            func_parts = line.split()
            func_idx = int(func_parts[-1])
            srcline_prefix = '@'
            src = []
            dbgprint(f'func_idx {func_idx}')
            
            line = sources.readline()
            while not (function_end in line):
                while not (srcline_prefix in line) and not (function_end in line):
                    line = sources.readline()
                if function_end in line:
                    break

                instr_line = sources.readline()
                line_parts = line[4:-3].split(',')
                dbgprint(f'LINE PARTS {line_parts}')
                instr = {}
                for l in line_parts:
                   k, v =  l.split(':') 
                   instr[ k.strip() ] = int(v)
                
                dbgprint(f'INSTRUCTION LINE {instr_line}')
                addr_part, inst_part = instr_line.split(';')
                instr_addr = addr_part.split(':')[0].split(" ")[-1]

                # instr_addr = re.findall(r'\d+', addr_part)[0] 
                dbgprint(f'instr_addr {instr_addr}')
                instr['addr'] =  int('0x' + instr_addr, 16)
                instr['type'] = inst_part.strip()
                src.append(instr) 
                line = sources.readline()

            dbgprint(f'source maps function {func_idx} src = {src}')
            sourcemaps[func_idx] = src
            line = sources.readline()

    return sourcemaps
# ; section "Code" (10)
# 0000028: 0a                                        ; section code
# 0000029: 00                                        ; section size (guess)
# 000002a: 03                                        ; num functions
# ; function body 0
# 000002b: 00                                        ; func body size (guess)
# 000002c: 00                                        ; local decl count
# 000002d: 0b                                        ; end
# 000002b: 02                                        ; FIXUP func body size
# ; function body 1
# 000002e: 00                                        ; func body size (guess)
# 000002f: 00                                        ; local decl count
# @ { line: 22, col_start: 9, col_end: 18 }
# 0000030: 20                                        ; local.get
        
def read_types(container, lines) -> None:
    types = []
    for type_line in lines:
        #line of the form '- type[2] (i32, f64)  -> i32'
        words = type_line.split()
        dbgprint(f'words {words}')

        assert len(words) >= 5, f'incorrect quantity found: expected 5 got {len(words)}'
        
        type_idx = ''.join(re.findall(r'\d+', words[1]))
        assert type_idx.isdigit()
        type_idx = int(type_idx)

        #str of the form (i32, f64) -> i32
        signature_str = ''.join(words[2:])
        params_str, results_str = signature_str.split('->')
        
        #remove () and transform to  list of types [i32, f64]
        params = [] if params_str == '()' else params_str[1:-1].split(',')
        results = results_str if results_str != 'nil' else None

        types.append({
            'params': params,
            'results': results,
            'idx': type_idx
        })

    dbgprint(f'All types {types}')
    container['types'] = types

def read_functions(container, lines):
# Function[3]:
#  - func[0] sig=0 <dummy>
#  - func[1] sig=2 <fac>
#  - func[2] sig=1 <fac5>
    funcs = []
    for fun_line in lines:
        words = fun_line.split()
        dbgprint(f'words {words}')

        #expected line e.g '- func[0] sig=0 <funcName>'
        assert len(words) >= 4, f'func definition incorrect format. Got {words}'

        func_idx_str = ''.join(re.findall(r'\d+', words[1]))
        func_idx = int(func_idx_str)
        sign_idx_str = words[2].split('=')[1]
        sign_idx = int(sign_idx_str)

        func_name = words[3]

        #remove '<' '>'chars
        func_name = func_name[1:-1] 
        funcs.append({'name': func_name, 'idx': func_idx, 'signature': sign_idx})

    dbgprint(f'All funcs {funcs}')
    container['funcs'] = funcs


def read_export(container , lines):
# Export[1]:
#  - func[2] <fac5> -> "main"
    exps = {}
    for line in lines:
        words = line.split()
        func_idx_str = ''.join(re.findall(r'\d+', words[1]))
        fun_idx = int(func_idx_str)
        export_name = words[-1]
        #remove quotes
        export_name = export_name[1:-1]
        exps[fun_idx] =  export_name

    dbgprint(f'All exports {exps}')
    container['exports'] = exps

def read_import(container, lines):
    pass

def read_code(container, lines):
# Code[3]:
#  - func[0] size=2 <dummy>
#  - func[1] size=28 <fac>
#  - func[2] size=21 <fac5 
    sizes = {}
    for line in lines:
        words = line.split()
        func_idx_str = ''.join(re.findall(r'\d+', words[1]))
        fun_idx = int(func_idx_str)

        _, size_str = words[2].split('=')
        size = int(size_str)
        sizes[fun_idx] = size

    dbgprint(f'All code sizes {sizes}')
    container['code_sizes'] = sizes

def read_custom(container, lines):
# Custom:
#  - name: "name"
#  - func[0] <dummy>
#  - func[1] <fac>
#  - func[2] <fac5>
#  - func[2] local[0] <int_32>
    pass


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
