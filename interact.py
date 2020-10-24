import math
import serial
from serial.tools import list_ports
from enum import Enum

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

def sum_hexs(off, ad):
    int_offs = int(off[2:], 16)
    int_ad = int(ad[2:], 16)
    return hex(int_offs + int_ad)

def rmv_off(dev, adr):
    int_offs = int(dev.getOffset()[2:], 16)
    int_ad = int(adr[2:], 16)
    return hex(int_ad - int_offs)


INTERUPT_TYPE = {
  "RUN" : '01',
  "HALT" : '02',
  "PAUSE" : '03',
  "STEP" : '04',
  "BPAdd" : '06',
  "BPRem" : '07',
  "DUMP" : '10',
  "DUMPLocals" : '11',
  "UPDATEFun" : '20',
  "UPDATELocal" : '21'
}


def toByte(dev, interupt_type, d=''):
    r = INTERUPT_TYPE[interupt_type]
    if len(d)>0:
        hx = sum_hexs(dev.getOffset(), d)[2:] #remove 0x
        _size = math.floor(len(hx) / 2)
        if _size % 2 != 0:
            print("WARNING: toByte not even addr\n")

        _hex_siz = hex(_size)[2:]
        if _size < 16:
            _hex_siz = '0' + _hex_siz
        r = r + _hex_siz + hx

    r +='\n'
    return r.upper().encode('ascii')

def run(dev):
    dev.send_data(toByte(dev, "RUN" ))

def halt(dev):
    dev.send_data(toByte(dev, "HALT" ))

def pause(dev):
    dev.send_data(toByte(dev, "PAUSE" ))

def step(dev):
    dev.send_data(toByte(dev, "STEP" ))

def add_bp(dev, bp):
    address = toByte(dev, "BPAdd", bp )
    dev.send_data(address)
    return address

def remove_bp(dev, bp):
    address = toByte(dev, "BPRem", bp )
    dev.send_data(address)
    return address

def dump(dev):
    dev.send_data(toByte(dev, "DUMP"))

def dump_local(dev):
    dev.send_data(toByte(dev, "DUMPLocals" ))

def update_fun(dev):
    dev.send_data(toByte(dev, "UPDATEFun" ))

def update_local(dev):
    dev.send_data(toByte(dev, "UPDATELocal" ))

