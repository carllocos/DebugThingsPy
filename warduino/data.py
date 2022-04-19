
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


PREFIX = 'test_data/'
def save_state(file_name: str, content: str) -> None:
    with open(PREFIX + file_name,"w" ) as f:
        f.write(content)

def state_blink_led():
    with open(PREFIX + 'blink.json', "r") as file:
        return file.read()

def fac_state():
    with open(PREFIX + 'fac_state.json', "r") as file:
        return file.read()
