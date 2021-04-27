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
    dbgs= []
    for c in filtered:
        d = load_device(c)
        deb = Debugger(d, mod)
        deb.policies = c.get('policies', [])
        dbgs.append(deb)

    _loc = next((d for d in dbgs if d.device.is_local), None)
    _rmt = next((d for d in dbgs if d.device.is_remote), None)
    if _loc is not None and config.get('proxy', False):
        if _rmt is None:
            raise ValueError(f'configuration error: function proxy requires a remote device. Enable a remote device')
        proxy_config = {}
        proxy_config['proxy'] = config.get('proxy', [])
        proxy_config['host'] = _rmt.device.host
        proxy_config['port'] = _rmt.device.port
        _loc.add_proxyconfig(proxy_config)
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


def load_config(path: Union[str, None] = None)-> None:
    if path is None:
        cwd = './'
        path = cwd + '.dbgconfig.json'
    config = None
    with open(path) as f:
        config = json.load(f)
    return config


if __name__ == "__main__":
    path = None
    config = load_config(path)
    if config is None:
        print("provide config file --config")
    else:

        dbg = start_dbg(config)
        if dbg is not None:
            rmt = dbg.remote_device
            loc = dbg.local_device
            if rmt is not None and rmt.device.uses_socket:
                s = rmt.device.medium