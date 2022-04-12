import inspect
import sys
import struct

from utils import util
import mylogger as log

END_MSG = ' \n'

Interrupts = {
    'addbp': '06',
    'dump': '60',
    'offset': '0x61',
    'locals': '11',
    'receivesession': '62',
    'recvproxies': '25',
    'rmvbp': '07',
    'run': '01',
    'step': '04',
    'until': '05',
    'updateModule' : '24',
    'pause': '03'
}


KINDS = {'pcState': '01',
         'bpsState': '02',
         'callstackState': '03',
         'globalsState': '04',
         'tblState': '05',
         'memState': '06', 
         'brtblState': '07',
         'stackvalsState': '08',
         'pcerrorState': '09'}


def serialize_wasm(interrupt, wasm, max_bytes):
    size = int2bytes(len(wasm), 4)
    ser = interrupt + size.hex() +  wasm.hex()
    return [ser.upper()]

def serialize_proxies(interrupt, host, port, func_ids, max_bytes):
    _func_amount = int2bytes(len(func_ids), 4).hex()
    _funcs = ''
    for i in func_ids:
        _funcs += int2bytes(i, 4).hex()
    _lenhost = int2bytes(len(host), 1).hex()
    _host =  host.encode().hex()
    _port = int2bytes(port, 4).hex()
    _sers = interrupt + _func_amount + _funcs + _port + _lenhost + _host
    return [_sers.upper()]

def encode_session(dssession, max_bytes):
    recv_int = Interrupts['receivesession']
    quanty_bytes_header = 1 + 4 #1 byte for interrupt (= 2 hexa chars) & 4 bytes for quantity bytes send (= 8 hexa chars)
    quanty_last_bytes = 2 #2 bytes, one to tell whether end or not and one for newline
    bytes_lost = quanty_bytes_header + quanty_last_bytes
    max_space = max_bytes - (bytes_lost * 2)
    #first recieve interrupt
    first_msg  = serialize_first_msg(dssession)

    chunks = [] 
    serialize_pc(dssession['pc'], chunks, max_space)
    # serialize_pc_error(dssession['pc_error'], chunks, max_space)
    serialize_breakpoints(dssession['breakpoints'], chunks, max_space)
    serialize_stackvalues(dssession['stack'], chunks, max_space)
    serialize_table(dssession['table'], chunks, max_space)
    serialize_callstack(dssession['callstack'], chunks, max_space)
    serialize_globals(dssession['globals'], chunks, max_space)
    serialize_memory(dssession['memory'], chunks, max_space)
    serialize_brtable(dssession['br_table'], chunks, max_space)

    # #log.stderr_print(f'len(chuncks)={len(chunks)} before adding first msg')
    chunks.insert(0, first_msg)
    last = len(chunks) - 1
    # #log.stderr_print(f'len(chuncks)={len(chunks)}')
    ds_chunks = []
    for i, c in enumerate(chunks):
        #log.stderr_print(f"chunk #{i}: {c}")
        done = '01' if i == last else '00'
        size = size_and_assert(c + done)
        size_ser = int2bytes(size, 4).hex()
        ds_chunks.append( recv_int + size_ser +  c + done)

    for i,c in enumerate(ds_chunks):
        if i == 0 and max_space < 74:
            #log.stderr_print(f'skipping assert on first_msg')
            continue
        assert len(c) <= max_bytes, f'chunk {i} of len {len(c)}'
        assert len(c) % 2 == 0, f'Not an even chars chunk {c}'
    encoded = [c.upper() for c in ds_chunks]
    assert len(encoded) >= 2, f'at least two messages expected got {len(encoded)}'
    return encoded


#PC serialization
def serialize_pc(pc_addr, chunks, max_space):
    #TODO add padding to the pointer to make even chars
    ##log.stderr_print(f"serialie_pc: {pc_addr}")
    #log.stderr_print(f"serialize {pc_addr}")
    kind = KINDS['pcState']
    (p, _) = serialize_pointer(pc_addr)
    pc_ser = kind + p 
    #log.stderr_print(f"pc_ser - {kind} {p}")
    add_in_chunks(chunks, pc_ser, max_space)

def serialize_pc_error(pc_addr, chunks, max_space):
    #TODO add padding to the pointer to make even chars
    ##log.stderr_print(f"serialie_pc: {pc_addr}")
    #log.stderr_print(f"serialize pc_error={pc_addr}")
    kind = KINDS['pcerrorState']
    if pc_addr is None:
        return
    (p, _) = serialize_pointer(pc_addr)
    pc_ser = kind + p 
    #log.stderr_print(f"pc_ser - {kind} {p}")
    add_in_chunks(chunks, pc_ser, max_space)

#helper serializers
def serialize_first_msg(session):

    #globals
    gls = session['globals']
    kind_globals = KINDS['globalsState']
    quantity_globals = int2bytes(len(gls), 4).hex()
    globals_ser = kind_globals + quantity_globals
    #log.stderr_print(f"serializeing globals {quantity_globals}")

    #Table
    tbl = session['table']
    kind_table = KINDS['tblState'] 
    tblinit_ser = int2bytes(tbl.get('init', 0), 4).hex()
    tblmax_ser = int2bytes(tbl.get('max', 0), 4).hex()
    tbl_size = int2bytes(len(tbl['elements']), 4).hex()
    tbl_ser = kind_table + tblinit_ser + tblmax_ser + tbl_size

   # memory
    kind_mem = KINDS['memState']
    mem = session['memory']
    minit_ser = int2bytes(mem.get('init', 0), 4).hex()
    mmax_ser = int2bytes(mem.get('max', 0), 4).hex()
    currentp_ser = int2bytes(mem['pages'], 4).hex()
    mem_ser = kind_mem + mmax_ser + minit_ser + currentp_ser

    return globals_ser + tbl_ser + mem_ser
 
def serialize_pointer(addr):
    ##log.stderr_print(f'serialize addr {addr} no offset {addr[2:]}')
    with_pad = make_evenaddr(addr)
    ##log.stderr_print(f'new addr 0x{with_pad}')
    size = int2bytes(len(with_pad) // 2, 1)
    ##log.stderr_print(f'size pointer {size} in hex {size.hex()} and addr {with_pad}')
    return (size.hex()+ with_pad, size)

def add_in_chunks(chunks, serialization, max_space):
    if len(chunks) > 0:
        last = chunks[-1]
        if len(last) + len(serialization) <= max_space:
            chunks[-1] = last + serialization
        else:
            chunks.append(serialization)
    else:
        chunks.append(serialization)

def int2bytes(i, quantity_bytes, byteorder = 'big'):
    return (i).to_bytes(quantity_bytes, byteorder) #'little'

def make_evenaddr(addr):
    noXo = addr[2:]
    chars_missing = len(noXo) %2
    if chars_missing == 0:
        return noXo
    else:
        return "0" * chars_missing + noXo

def serialize_breakpoints(bps, chunks, max_space):
    #log.stderr_print(f'serializing bps {bps}')
    kind = KINDS['bpsState']
    header_len = len(kind) + 2# 2 chars needed to express quantity of breakpoints
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    bps_ser = ""
    quantity_bps = 0

    def add_chunk():
        nonlocal kind, quantity_bps, bps_ser, current_chunk
        header = kind + int2bytes(quantity_bps, 1).hex()
        ##log.stderr_print(f'making chunk for #{quantity_bps} bps')
        ##log.stderr_print(f'header {header} - {bps_ser}')
        ##log.stderr_print(f'current_chunk {current_chunk}')
        chunks.append(current_chunk + header + bps_ser)

    for bp in bps:
        (_serbp, _) = serialize_pointer(bp)
        if max_space <  len(current_chunk) + header_len + len(bps_ser) + len(_serbp):
            ##log.stderr_print(f'call whitin for add_chunk: bp not added yet {bp} with ser {_serbp}')
            if bps_ser != '':
                add_chunk()
            else:
                ##log.stderr_print("in the else")
                chunks.append(current_chunk)
            quantity_bps = 0
            bps_ser = ""
            current_chunk = ""

        quantity_bps += 1
        bps_ser += _serbp

    if bps_ser != "":
        ##log.stderr_print("breakpoints_ser: call from outsite for")
        add_chunk()
    elif current_chunk != "":
        chunks.append(current_chunk)

def serialize_stackValue(vobj):
        t = int2bytes(valtype2int(vobj['type']), 1).hex()
        v =  val2bytes(vobj['type'], vobj['value']).hex()
        return t + v

def serialize_stackvalues(vals, chunks, max_space):
    #log.stderr_print(f'#{len(vals)} Stack Values')
    #log.stderr_print(f'Chunks={chunks}')
    kind = KINDS['stackvalsState']
    header_len = len(kind) + 4# 4 chars for quantity stack values
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    quantity_sv = 0
    vals_ser = ""
    #  #log.stderr_print(f"chunck used #{len(current_chunk)}")
    def add_chunk():
        nonlocal kind, quantity_sv, vals_ser, current_chunk
        #  #log.stderr_print(f'making chunk for #{quantity_sv} values')
        header = kind + int2bytes(quantity_sv, 2).hex()
        chunks.append(current_chunk + header + vals_ser)
        #  #log.stderr_print(f'chunk idx {len(chunks) -1} chunk {len(chunks[-1])}')
        assert len(chunks[-1]) <= max_space, f'failed for chunk idx {len(chunks) -1 } #{len(chunks[-1])}'

    for vobj in vals:
        #  t = int2bytes(valtype2int(vobj['type']), 1).hex()
        #  v =  val2bytes(vobj['type'], vobj['value']).hex()
        #  _serval = t + v
        _serval = serialize_stackValue(vobj)
        if max_space < len(current_chunk) + header_len + len(vals_ser) + len(_serval) :
            if vals_ser != '':
                add_chunk()
            else:
                #log.stderr_print("in the else")
                chunks.append(current_chunk)
            quantity_sv = 0
            vals_ser = ""
            current_chunk = ""
        
        quantity_sv +=1
        vals_ser += _serval
    
    if vals_ser != "":
        add_chunk()
    elif current_chunk != "":
        #log.stderr_print("in the elif")
        chunks.append(current_chunk)
    #log.stderr_print(f'Chunks={chunks}')

def serialize_globals(vals, chunks, max_space):
    #'globals': [{'idx': 0, 'type': 'i32', 'value': 0}, {'idx': 1, 'type': 'i32', 'value': 0}, {'idx': 2, 'type': 'i32', 'value': 88}],
    #  #log.stderr_print(f'serializing globals #{len(vals)} - globals - {vals}')
    kind = KINDS['globalsState']
    #log.stderr_print(f'Chunks={chunks}')
    header_len = len(kind) + 8# 8 chars for quantity globals values
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    quantity_globals = 0
    vals_ser = ""
    #  #log.stderr_print(f"chunck used #{len(current_chunk)}")
    def add_global_chunck():
        nonlocal current_chunk, kind, quantity_globals, vals_ser
        #log.stderr_print(f'making chunk for #{quantity_globals} values')
        header = kind + int2bytes(quantity_globals, 4).hex()
        chunks.append(current_chunk + header + vals_ser)
        #log.stderr_print(f'chunk idx {len(chunks) -1} chunk {len(chunks[-1])}')
        assert len(chunks[-1]) <= max_space, f'failed for chunk idx {len(chunks) -1 } #{len(chunks[-1])}'

    for vobj in vals:
        _serval = serialize_stackValue(vobj)
        if max_space < len(current_chunk) + header_len + len(vals_ser) + len(_serval) :
            if vals_ser != '':
                add_global_chunck()
            else:
                #log.stderr_print("in the else")
                chunks.append(current_chunk)
            quantity_globals = 0
            vals_ser = ""
            current_chunk = ""
        
        quantity_globals +=1
        vals_ser += _serval
    
    if vals_ser != "":
        add_global_chunck()
    elif current_chunk != "":
        #log.stderr_print("in the elif")
        chunks.append(current_chunk)
    #log.stderr_print(f'Chunks={chunks}')

def serialize_table(tbl, chunks, max_space):
    #  #log.stderr_print(f"serializing  #{len(tbl['elements'])} elements with {tbl}")
    kind = KINDS['tblState']
    #log.stderr_print(f'Chunks={chunks}')
    funref = 17
    elem_type_bytes = 1 #1 byte to hold which kind of elements hold in table. Although for now only funcrefs
    elems_quantity_bytes = 4 #quantity bytes used to express quantity of elements
    header_len = len(kind) + (elem_type_bytes + elems_quantity_bytes) * 2 

    ##log.stderr_print(f'header len {header_len}')
    quantity = 0
    elems_ser = ""
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    ##log.stderr_print(f'current_chunk #{len(current_chunk)}')

    def chunk_tbl():
        nonlocal kind, quantity, elems_ser, current_chunk, elem_type_bytes, elems_quantity_bytes, funref
        quanty_hex = int2bytes(quantity, elems_quantity_bytes, byteorder='big').hex()
        elems_type_hex = int2bytes(funref, elem_type_bytes, byteorder='big').hex()
        header = kind + elems_type_hex + quanty_hex
        chunks.append(current_chunk + header + elems_ser)
        #  #log.stderr_print(f'CARLOS adding {quantity} elemts')
        ##log.stderr_print(f'chunk idx {len(chunks) -1} chunk {len(chunks[-1])}')
        assert len(chunks[-1]) <= max_space, f'failed for chunk idx {len(chunks) -1 } #{len(chunks[-1])}'

    for e in tbl['elements']:
        e_ser = int2bytes(e, 4, byteorder='big').hex()
        ##log.stderr_print(f'{max_space} < {len(current_chunk)} + {header_len}+ {len(elems_ser)} + {len(e_ser)}')
        if max_space < len(current_chunk) + header_len + len(elems_ser) + len(e_ser):
            if elems_ser != '':
                #  #log.stderr_print("CARLOS lalala")
                chunk_tbl()
            else:
                #  #log.stderr_print("CARLOS in the else")
                chunks.append(current_chunk)
            quantity = 0
            elems_ser = ""
            current_chunk = ""
        
        quantity +=1
        elems_ser += e_ser

    if elems_ser != "":
        #  #log.stderr_print("CARLOS llooooo")
        chunk_tbl()
    elif current_chunk != "":
        #  #log.stderr_print("CARLOS YAAAY")
        chunks.append(current_chunk)
    ##log.stderr_print(f'total chunks {len(chunks)}')
    #log.stderr_print(f'Chunks={chunks}')

def serialize_callstack(callstack, chunks, max_space):
    #log.stderr_print(f'serialzing #{len(callstack)} frames')
    #log.stderr_print(f'Chunks={chunks}')

    kind = KINDS['callstackState']
    header_len = len(kind) + 4# 4 chars for quantity stack values
    current_chunk = chunks.pop(-1) if chunks and len(chunks[-1]) < max_space else ""
    quantity = 0
    frames_ser = ""
    #  #log.stderr_print(f"chunck used #{len(current_chunk)} {current_chunk}")
    dbgframes = []

    def chunk_callstack():
        nonlocal kind, quantity, frames_ser, current_chunk
        quantity_ser = int2bytes(quantity, 2).hex()
        header = kind + quantity_ser
        #  #log.stderr_print(f"chunk for #{quantity} frames")
        chunks.append(current_chunk + header + frames_ser)
        #  for i,f in enumerate(dbgframes):
        #      #log.stderr_print(f'i:{i} frame {f}')

    for frame in callstack:

        type_ser = int2bytes(frame['type'], 1).hex()
        sp_ser = signedint2bytes(frame['sp'], 4).hex()
        fp_ser = signedint2bytes(frame['fp'], 4).hex()
        (retaddr_ser, _) = serialize_pointer(frame['ra'])
        frame_ser = type_ser + sp_ser + fp_ser + retaddr_ser
        if isfunc_type(frame):
            fid = int(frame['fidx'], 16) #FIXME do we really get hex at this level?
            funcid_ser = int2bytes( fid, 4).hex()
            frame_ser += funcid_ser
        else:
            (blockaddr_ser, _) = serialize_pointer(frame['block_key'])
            frame_ser += blockaddr_ser

        ##log.stderr_print(f'frame {frame} - {frame_ser}')
        if max_space < len(current_chunk) + header_len + len(frames_ser) + len(frame_ser) :
            if frames_ser != '':
                #  #log.stderr_print("FRAMES_CARL in the TRue")
                chunk_callstack()
            else:
                #  #log.stderr_print("FRAMES_CARL in the else")
                chunks.append(current_chunk)
            quantity = 0
            frames_ser = ""
            current_chunk = ""
            dbgframes = []
        #  #log.stderr_print(f'adding one frame of #{len(frame_ser)}')
        dbgframes.append(frame)
        quantity += 1
        frames_ser += frame_ser
    
    if frames_ser != "":
        #  #log.stderr_print("FRAMES_CARL in the outer true")
        chunk_callstack()
    elif current_chunk != "":
        #  #log.stderr_print("FRAMES_CARL in the outer elif")
        chunks.append(current_chunk)
    #log.stderr_print(f'Chunks={chunks}')

def serialize_brtable(br_table, chunks, max_space):
    #output of the form
    # Header                        |  
    # ------------------------------|
    #  1 byte |  2 bytes  | 2 bytes | uint32        |
    #|br_table| begin idx | end idx | br_table elem | ...
    #  #log.stderr_print(f'serializing br_table #{len(br_table["labels"])}')
    assert br_table['size'] == len(br_table['labels'])
    #log.stderr_print(f'Chunks={chunks}')
    header_bytes = 5
    header_len =  header_bytes * 2
    br_tbl_elem_len = 4 * 2 #4 bytes to per elem

    current_chunk = ""
    if chunks and (len(chunks[-1]) + header_len + br_tbl_elem_len) <= max_space:
        #space for at least one br_table elem in previous chunk
        current_chunk = chunks.pop(-1)

    begin_idx = 0
    end_idx = 0

    elems_ser = list(map(lambda v: int2bytes(v, quantity_bytes=4).hex(), br_table['labels']))

    while end_idx < br_table['size']:
        free_space = (max_space - len(current_chunk) - header_len) // br_tbl_elem_len
        end_idx = begin_idx + free_space
        if end_idx > br_table['size']:
            end_idx = br_table['size']

        elems = elems_ser[begin_idx : end_idx]
        vals_ser = ''.join(elems)

        beg_ser = int2bytes(begin_idx, quantity_bytes=2).hex()
        end_ser = int2bytes(begin_idx + (len(elems) - 1), quantity_bytes=2).hex()
        header = KINDS['brtblState'] + beg_ser + end_ser
        chunks.append(current_chunk + header + vals_ser)

        assert len(chunks[-1]) <= max_space

        current_chunk = ""
        begin_idx = end_idx
    #log.stderr_print(f'Chunks={chunks}')

def serialize_memory(memory, chunks, max_space):
    #output of the form
    # Header                        |  
    # ------------------------------|
    #  1 byte |  4 bytes     | 4 bytes    |  bytes size = end offset - begin offset + 1 
    #| memory | begin offset | end offset | bytes  ...
    #log.stderr_print(f'serializing memory #{len(memory["bytes"])} bytes') #TODO replace total, with the use of pages
    #log.stderr_print(f'Chunks={chunks}')
    header_bytes = 9
    header_len =  header_bytes * 2
    memcell_len = 1 * 2 #1 byte per memory cell
    if memory['pages'] == 0:
        return
    if len(memory['bytes']) == 0:
        #log.stderr_print('BYTES SHOULD NOT BE EMPTY!!!!!!!')
        return
    current_chunk = ""
    if chunks and (len(chunks[-1]) + header_len + memcell_len ) <= max_space:
        #space for at least 1 memory cells in previous chunk
        #  #log.stderr_print(f'using exiting chunck')
        current_chunk = chunks.pop(-1)

    begin_off = 0
    end_off = 0
    mem_bytes = memory['bytes']
    # mem_bytes = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x11\x11\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    total_bytes = len(mem_bytes)

    while end_off < total_bytes:
        free_space = (max_space - len(current_chunk) - header_len) // memcell_len
        end_off = end_off + free_space
        if end_off > total_bytes:
            end_off = total_bytes

        _bytes = mem_bytes[begin_off : end_off]
        bytes_ser = _bytes.hex()
        beg_ser = int2bytes(begin_off, quantity_bytes=4).hex()
        end_ser = int2bytes(begin_off + (len(_bytes) - 1), quantity_bytes=4).hex()
        header = KINDS['memState'] + beg_ser + end_ser
        chunks.append(current_chunk + header + bytes_ser)

        assert len(chunks[-1]) <= max_space

        current_chunk = ""
        begin_off = end_off
    #log.stderr_print(f'Chunks={chunks}')

def size_and_assert(ser):
    l = len(ser)
    assert l % 2 == 0, f'no even size for serialialization {ser}'

    return l // 2

def valtype2int(t):
    if t == 'i32':
        return 0
    elif t == 'i64':
        return 1
    elif t == 'f32':
        return 2

    elif t == 'f64':
        return 3
    else:
        errprint(f"Unknwon stack value type {t}")

def val2bytes(value_type, val):
    qb = 4 if value_type[1:] == '32' else 8
    if value_type[0] == 'i':
        #  ##log.stderr_print(f'serializing {value_type}')
        return int2bytes(val, qb, byteorder='little')
    else:
        #float case
        return float2bytes(val, qb, byteorder='little')

def float2bytes(val, quantity, byteorder = 'big'):

    if quantity not in [4, 8]:
        raise ValueError(f'requested incorrect quantity of bytes {quantity}')

    #get 4 byte single precision with struct
    #'>' big endian
    fmt = 'f' if quantity == 4 else 'd'
    fmt = ('>' if byteorder == 'big' else '<') + fmt

    #  ##log.stderr_print(f"formating value with {fmt}")
    b = struct.pack(fmt, val) 
    #  ##log.stderr_print(f'value {val} becomes {b}')
    return b

def isfunc_type(frame):
    return frame['type'] == 0

def signedint2bytes(i, quantity, byteorder='big'):
    return (i).to_bytes(quantity, byteorder, signed = True)
