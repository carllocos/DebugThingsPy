
def snapshots_equal(s1, s2):
    rebase_sn1 = lambda addr: int(addr, 16) - int(s1['start'][0], 16)
    rebase_sn2 = lambda addr: int(addr, 16) - int(s2['start'][0], 16)

    assert rebase_sn1(s1['pc']) == rebase_sn2(s2['pc']), 'PC are not equal'

    assert len(s1['breakpoints']) == len(s2['breakpoints']), "not equal amount bps"
    bps1 = [rebase_sn1(bp) for bp in s1['breakpoints']]
    bps2 = [rebase_sn2(bp) for bp in s2['breakpoints']]
    bps1.sort()
    bps2.sort()
    assert bps1 == bps2, 'unequal {bps1} != {bps2}'

    stack1 = s1['stack']
    stack1.sort(key=lambda f: f['idx'])
    stack2 = s2['stack']
    stack2.sort(key=lambda f: f['idx'])
    for sv1, sv2 in zip(stack1, stack2):
        assert sv1['idx'] == sv2['idx'], f"frame idx {sv1} {sv2}"
        assert sv1['type'] == sv2['type'], f"frame type {sv1} {sv2}"
        assert sv1['value'] == sv2['value'], f"frame value {sv1} {sv2}"

    frames1 = s1['callstack']
    frames1.sort(key=lambda f: f['idx'])
    frames2 = s2['callstack']
    frames2.sort(key=lambda f: f['idx'])
    for f1, f2 in zip(frames1, frames2):

        assert f1['type'] == f2['type'], f"unequal type {f1} {f2}"
        assert f1['fidx'] == f2['fidx'], f"unequal fidx {f1} {f2}"
        assert f1['sp'] == f2['sp'], f"unequal sp {f1} {f2}"
        assert f1['fp'] == f2['fp'], f"unequal fp {f1} {f2}"
        if f1['type'] == 0:
            assert f1['block_key'] == f2['block_key'], f"unequal block_key {f1} {f2}"
        else:
            assert rebase_sn1(f1['block_key']) == rebase_sn2(f2['block_key']), f"unequal block_key {f1} {f2} - without offset bk1={rebase_sn1(f1['block_key'])} bk2={rebase_sn2(f2['block_key'])}"

        assert rebase_sn1(f1['ra']) == rebase_sn2(f2['ra']), f"unequal ra {f1} {f2} - without offset f1_ra={rebase_sn1(f1['ra'])} f2_ra={rebase_sn2(f2['ra'])}"

    gb1 = s1['globals']
    gb1.sort(key=lambda g: g['idx'])
    gb2 = s2['globals']
    gb2.sort(key=lambda g: g['idx'])
    assert len(gb1) == len(gb2), "not equal amount of globals"
    for gv1, gv2 in zip(gb1, gb2):
        assert gv1 == gv2, f'unequal global values {gv1} != {gv2}'

    tbl1 = s1['table']
    tbl2 = s2['table']
    assert tbl1['max'] == tbl2['max'], f"unequal max table {tbl1['max']}!={tbl2['max']}"
    assert tbl1['init'] == tbl2['init'], f"unequal init table {tbl1['init']}!={tbl2['init']}"
    assert tbl1['elements'] == tbl2['elements'], f"unequal elements table {tbl1['elements']}!={tbl2['elements']}"


    mem1 = s1['memory']
    mem2 = s2['memory']
    assert mem1['max'] == mem2['max'], f"unequal max memory {mem1['max']}!={mem2['max']}"
    assert mem1['init'] == mem2['init'], f"unequal init memory {mem1['init']}!={mem2['init']}"
    assert mem1['pages'] == mem2['pages'], f"unequal pages memory {mem1['pages']}!={mem2['pages']}"
    assert mem1['bytes'] == mem2['bytes'], f"unequal bytes memory {mem1['bytes']}!={mem2['bytes']}"

    br_tbl1 = s1['br_table']
    br_tbl2 = s2['br_table']
    assert br_tbl1['size'] == br_tbl2['size'], f"unequal size br_table {br_tbl1['size']}!={br_tbl2['size']}"
    assert br_tbl1['labels'] == br_tbl2['labels'], f"unequal labels br_table {br_tbl1['labels']}!={br_tbl2['labels']}"

def state_blink_led():
    labels = b'\x00' * 1024
    return {'pc': '0x600002dd00a6', 'start': ['0x600002dd0000'], 'breakpoints': [], 'stack': [{'idx': 0, 'type': 'i32', 'value': 1000}], 'callstack': [{'type': 0, 'fidx': '0x4', 'sp': -1, 'fp': -1, 'block_key': '0x0', 'ra': '0x600002dd006f', 'idx': 0}, {'type': 3, 'fidx': '0x0', 'sp': 0, 'fp': 0, 'block_key': '0x600002dd0090', 'ra': '0x600002dd0092', 'idx': 1}], 'globals': [{'idx': 0, 'type': 'i32', 'value': 23}, {'idx': 1, 'type': 'i32', 'value': 1}, {'idx': 2, 'type': 'i32', 'value': 0}], 'table': {'max': 0, 'init': 0, 'elements': b''}, 'memory': {'pages': 0, 'max': 0, 'init': 0, 'bytes': b''}, 'br_table': {'size': '0x100', 'labels': labels}}


def fac_state():
    labels = b'\x00' * 1024
    mem_bytes = b'\x00' * 65536 * 2 # 2 memory pages
    return {'pc': '0x6000011f0065', 'start': ['0x6000011f0000'], 'breakpoints': [], 'stack': [{'idx': 0, 'type': 'i32', 'value': 5}, {'idx': 1, 'type': 'i32', 'value': 5}, {'idx': 2, 'type': 'i32', 'value': 4}, {'idx': 3, 'type': 'i32', 'value': 3}], 'callstack': [{'type': 0, 'fidx': '0x3', 'sp': -1, 'fp': -1, 'block_key': '0x0', 'ra': '0x6000011f005a', 'idx': 0}, {'type': 3, 'fidx': '0x0', 'sp': 0, 'fp': 0, 'block_key': '0x6000011f0083', 'ra': '0x6000011f0085', 'idx': 1}, {'type': 0, 'fidx': '0x2', 'sp': 0, 'fp': 0, 'block_key': '0x0', 'ra': '0x6000011f0089', 'idx': 2}, {'type': 4, 'fidx': '0x0', 'sp': 2, 'fp': 1, 'block_key': '0x6000011f006a', 'ra': '0x6000011f006c', 'idx': 3}, {'type': 0, 'fidx': '0x2', 'sp': 1, 'fp': 1, 'block_key': '0x0', 'ra': '0x6000011f0073', 'idx': 4}, {'type': 4, 'fidx': '0x0', 'sp': 3, 'fp': 2, 'block_key': '0x6000011f006a', 'ra': '0x6000011f006c', 'idx': 5}, {'type': 0, 'fidx': '0x2', 'sp': 2, 'fp': 2, 'block_key': '0x0', 'ra': '0x6000011f0073', 'idx': 6}], 'globals': [{'idx': 0, 'type': 'i32', 'value': 0}, {'idx': 1, 'type': 'i32', 'value': 0}], 'table': {'max': 2, 'init': 2, 'elements': b'\x02\x00\x00\x00\x01\x00\x00\x00'}, 'memory': {'pages': 2, 'max': 32768, 'init': 2, 'bytes': mem_bytes}, 'br_table': {'size': '0x100', 'labels': labels}}
