from boards import m5stickc as board
from discovery import serial as discovery
from communication import serial as ser
from communication import interact


def debug_m5StickC():
    config = board.M5StickC.serialConfig()
    dev = discovery.find_device(config)
    if not dev:
        print('failed to find desired device')
        return

    serializer = board.M5StickC.serializer()
    medium = ser.Serial(serializer)
    inter = interact.Interact(dev=dev, serializer=serializer, medium=medium)
    inter.intialize('dummy')
    return inter


def clean():
    print(inter.get_serial().read_until(b'\n'))

inter = debug_m5StickC()
