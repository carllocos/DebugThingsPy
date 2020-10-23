import serial
from serial.tools import list_ports

import device

def find_device(device_config):
    for d in list_devices():
        if d.list_port_info().device != device_config.device:
            continue
        d.set_config(device_config)
        return d

def list_devices():
    return [device.Device(lpi) for lpi in list_ports.comports()]

def print_devices(devs = None):
    devs = devs if devs else list_devices()
    for idx, d in enumerate(devs):
        print(f'idx: {idx}\t{d}')
#API WARDUINO see file interrupt_operations.cpp


def run(dev):
    d=b'01\n'
    dev.send_data(d)

def halt(dev):
#  interruptHALT = 0x02,
    pass

def pause(dev):
    d = b'03\n'
    dev.send_data(d)
    #  dev.send_data(bytes([3]))

def step(dev):
#  interruptSTEP = 0x04,
    pass
def add_breakpoint(dev):
#  interruptBPAdd = 0x06,
    pass
def remove_breakpoint(dev):
#  interruptBPRem = 0x07,
    pass
def dump(dev):
#  interruptDUMP = 0x10,
    pass
def dump_local(dev):
#  interruptDUMPLocals = 0x11,
    pass
def update_fun(dev):
#  interruptUPDATEFun = 0x20,
    pass
def update_local(dev):
#  interruptUPDATELocal = 0x21
    pass

