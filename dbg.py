from __future__ import annotations
from typing import Union
import json
# import argparse

from web_assembly import WAModule
from boards import load_device
from things import Debugger

dbg = None
bp_loop = '0x9d'
bp_else = '0x72'
bp_postfac = '0xa9'
rmt = None
loc = None
ds_loc = None
ds_rmt = None
mod = None

def start_dbg(config: json):
    global mod

    mod = WAModule.from_file(config['program'], out=config['out'])
    filtered = filter(lambda c: c.get('enable', True), config['devices'])
    devices = map(load_device, filtered)

    dbgs = map(lambda d: Debugger(d, mod), devices)
    _loc = next((d for d in dbgs if d.device.is_local), None)
    _rmt = next((d for d in dbgs if d.device.is_remote), None)
    return Test(_rmt, _loc)

class Test():
    def __init__(self, rmt, loc):
        self.__rmt = rmt
        self.__loc = loc

    @property
    def remote_device(self):
        return self.__rmt

    @property
    def local_device(self):
        return self.__loc


def asksessions():
    global ds_loc, ds_rmt, dbg
    ds_loc = dbg.local_device.debug_session()
    ds_rmt = dbg.remote_device.debug_session()

def load_config(path: Union[str, None] = None)-> None:
    if path is None:
        cwd = './'
        path = cwd + '.dbgconfig.json'
    config = None
    with open(path) as f:
        config = json.load(f)
    return config


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(prefix_chars='-')
    # parser.add_argument('-l', '--local')
    # parser.add_argument('-r', '--remote')
    # options = parser.parse_args()

    path = None
    config = load_config(path)
    if config is None:
        print("provide config file --config")
    else:
        dbg = start_dbg(config)
        if dbg is not None:
            rmt = dbg.remote_device
            loc = dbg.local_device
            loc.connect()
            # loc.commit()
            [i] = mod.codes.linenr(52)
        #     f = mod.functions["fac"]
        #     [else_ins]  = f.code[41]
        #     fm = mod.functions["main"]
        #     [call_fac] = fm.code[54]
        #     loc.add_breakpoint(call_fac)
    # all_enabled = options.local is None and options.remote is None
    # with_local_dev = options.local is not None or all_enabled
    # with_rmt_dev = options.remote is not None or all_enabled

#  loc = dbg.local_device
#  loc.receive_session_test()
