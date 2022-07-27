from __future__ import annotations
from typing import Union
import json

# import argparse

from web_assembly import WAModule
from boards import load_device
from things import Debugger

dbg = None
bp_loop = "0x9d"
bp_else = "0x72"
bp_postfac = "0xa9"
rmt = None
loc = None
ds_loc = None
ds_rmt = None
mod = None


def test_update_proxies():
    global loc, rmt

    loc.connect()
    loc.upload_module(mod)
    loc.upload_proxies()


def start_dbg(config: dict):
    global mod

    mod = WAModule.from_file(config["program"], out=config["out"])
    filtered = filter(lambda c: c.get("enable", True), config["devices"])
    dbgs = []
    _rmt = None
    _loc = None
    for c in filtered:
        d = load_device(c)
        deb = Debugger(d, mod)
        deb.policies = c.get("policy", [])
        dbgs.append(deb)

        if c.get("is_remote", False):
            _rmt = deb
        else:
            _loc = deb
    # _loc = next((d for d in dbgs if d.device.is_local), None)
    # _rmt = next((d for d in dbgs if d.device.is_remote), None)
    if _loc is not None:
        # if _rmt is None:
        #     raise ValueError(
        #         f"configuration error: function proxy requires a remote device. Enable a remote device"
        #     )
        proxy_config = {}
        proxy_config["proxy"] = config.get("proxy", [])
        proxy_config["host"] = _rmt.device.host
        proxy_config["port"] = _rmt.device.port
        _loc.add_proxyconfig(proxy_config)
    return Test(_rmt, _loc)


class Test:
    def __init__(self, rmt, loc):
        self.__rmt = rmt
        self.__loc = loc

    @property
    def remote_device(self):
        return self.__rmt

    @property
    def local_device(self):
        return self.__loc


def load_config(path: Union[str, None] = None) -> None:
    if path is None:
        cwd = "./"
        path = cwd + ".dbgconfig.json"
    config = None
    with open(path) as f:
        config = json.load(f)
    return config


def space_needed(arg):
    frames = 2 * (arg + 1) + 2
    vals = arg + 1
    default = 0x100

    callstack_size = default
    stack_size = default

    counter1 = 0
    counter2 = 0
    while callstack_size < frames:
        counter1 += 1
        callstack_size += 256

    while stack_size < vals:
        counter2 += 1
        stack_size += 256
    obj = {
        "callstack_size_below": hex(callstack_size - 256),
        "cs_increase": counter1 - 1,
        "stack_size_below": hex(stack_size - 256),
        "stack_increase": counter2 - 1,
    }
    print(obj)

    return {
        "frames": frames,
        "stack": vals,
        "callstack_size": hex(callstack_size),
        "cs_increase": counter1,
        "stack_size": hex(stack_size),
        "stack_increase": counter2,
    }


def accurate_size(arg):
    frames = 2 * (arg + 1) + 2
    vals = arg + 1
    return {
        "frames": frames,
        "frames_hex": hex(frames),
        "stack": vals,
        "stack_hex": hex(vals),
    }


def benchmark_experiment3(arg):
    import os
    import time

    dev = rmt
    dev.connect()
    [i] = mod.linenr(27)
    dev.add_breakpoint(i)
    dev.run()

    while dev.session is None:
        print("waiting until bp is reached...")
        time.sleep(0.5)

    outputfile = "decr_debugsession_sizes.csv"
    callstack_size = 2 * (arg + 1) + 2
    with open(outputfile, "a") as file:
        st = os.stat(outputfile)
        if st.st_size == 0:
            file.write(f"arg,callstack,session_size\n")
        print(
            f"arg={arg},callstack={callstack_size},session_size={dev.session.total_size}\n"
        )
        file.write(f"{arg},{callstack_size},{dev.session.total_size}\n")


def benchmark_experiment2(arg, isStack5=True, default_size_exceeded=False):
    import time

    output_name = ""
    device = "stack5" if isStack5 else "stickc"
    if default_size_exceeded:
        output_name = f"exceeded_{device}_decr_" + str(arg) + ".csv"
    else:
        output_name = f"{device}_decr_" + str(arg) + ".csv"

    [i] = mod.linenr(27)

    dev = rmt
    dev.bench_name(output_name)
    dev.connect()
    dev.add_breakpoint(i)
    dev.run()
    total_runs = 30
    for i in range(total_runs):
        while dev.session is None or dev.session.version != i:
            print("sleeping 0.5secs")
            time.sleep(0.5)

        assert dev.session.version == i, f"incorrect {dev.session.version} != {i}"

        if i != (total_runs - 1):
            print(f"Send Run {i}")
            dev.run()

    expected_frames = 2 * (arg + 1) + 2
    l = len(dev.session.callstack.all_frames)
    reached = "reached" if expected_frames == l else f"not reached. Got {l}"
    print(
        f"done bechmark_COUNT_LIMITS file={output_name}, Expected frames={expected_frames} {reached}"
    )
    if dev.session.exception:
        print(f"exception occurred: {dev.session.exception}")
        return


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
