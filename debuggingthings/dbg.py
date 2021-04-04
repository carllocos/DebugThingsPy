import argparse

from boards import m5stickc as board
from discovery import serial as discovery
from discovery import sock as discoverySock
from communication import serial as ser
from communication import sock as sockCom
from things import debug


def connect(use_localdev, use_rmtdev):

    dbgrmt = None
    rmt_dev = None
    if use_rmtdev:
        print('searching for remote device')
        config = board.M5StickC.serialConfig()
        rmt_dev = discovery.find_device(config)

        if not rmt_dev:
            print('failed to find desired device')
            return
    else:
        print('do not use_rmtdev')

    loc_dev = None
    dbglocal = None
    if use_localdev:
        print('searching for local device')
        loc_sock = board.M5StickC.socketConfig()
        loc_dev = discoverySock.find_device(loc_sock)

        if loc_dev is None:
            print("failed to locate local device")
            return None
    else:
        print('do not use_localdev')

    if use_rmtdev:
        print('connecting to remote device')
        serializer = board.M5StickC.serializer()
        medium = ser.Serial(serializer)
        dbgrmt = debug.Debugger(dev=rmt_dev, serializer=serializer, medium=medium)
        dbgrmt.intialize('dummy')

    if use_localdev:
        print('connecting to local device')
        sockSer = board.M5StickC.sockSerializer()
        sock_med =  sockCom.Socket(sockSer)
        dbglocal = debug.Debugger(dev=loc_dev,  serializer = sockSer, medium=sock_med)
        dbglocal.intialize('dummy')

    return Test(dbgrmt, dbglocal)

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

dbg = None
bp_loop = '0x9d'
bp_else = '0x72'
bp_postfac = '0xa9'
rmt = None
loc = None
ds_loc = None
ds_rmt = None

def asksessions():
    global ds_loc, ds_rmt, dbg
    ds_loc = dbg.local_device.debug_session()
    ds_rmt = dbg.remote_device.debug_session()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prefix_chars='-')
    parser.add_argument('-l', '--local')
    parser.add_argument('-r', '--remote')
    options = parser.parse_args()
    
    all_enabled = options.local is None and options.remote is None
    with_local_dev = options.local is not None or all_enabled
    with_rmt_dev = options.remote is not None or all_enabled
    dbg = connect(with_local_dev, with_rmt_dev)
    if dbg is not None:
        rmt = dbg.remote_device
        loc = dbg.local_device
#  loc = dbg.local_device
#  loc.receive_session_test()
