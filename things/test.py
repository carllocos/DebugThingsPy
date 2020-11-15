from boards import m5stickc as board
from discovery import serial as discovery
from communication import serial as ser
from things import debug


def debug_m5StickC():
    config = board.M5StickC.serialConfig()
    dev = discovery.find_device(config)
    if not dev:
        print('failed to find desired device')
        return

    serializer = board.M5StickC.serializer()
    medium = ser.Serial(serializer)
    dbg = debug.Debugger(dev=dev, serializer=serializer, medium=medium)
    dbg.intialize('dummy')
    return dbg


def clean():
    print(dbg.get_serial().read_until(b'\n'))

dbg = debug_m5StickC()
