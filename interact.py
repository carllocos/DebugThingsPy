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


def toAddr(dev, interupt_type, d=''):
    r = INTERUPT_TYPE[interupt_type]
    if len(d)>0:
        hx = sum_hexs(dev.getOffset(), d)[2:] #remove 0x
        _size = math.floor(len(hx) / 2)
        if _size % 2 != 0:
            print("WARNING: toAddr not even addr\n")

        _hex_siz = hex(_size)[2:]
        if _size < 16:
            _hex_siz = '0' + _hex_siz
        r = r + _hex_siz + hx

    r +='\n'
    return r.upper().encode('ascii')

def run(dev):
    dev.send_data(toAddr(dev, "RUN" ))

def halt(dev):
    dev.send_data(toAddr(dev, "HALT" ))

def pause(dev):
    dev.send_data(toAddr(dev, "PAUSE" ))

def step(dev):
    dev.send_data(toAddr(dev, "STEP" ))

def add_bp(dev, bp):
    address = toAddr(dev, "BPAdd", bp )
    dev.send_data(address)
    return address

def remove_bp(dev, bp):
    address = toAddr(dev, "BPRem", bp )
    dev.send_data(address)
    return address

def dump(dev):
    dev.send_data(toAddr(dev, "DUMP"))

def dump_local(dev, qf = 1):
    data = INTERUPT_TYPE['DUMPLocals']
    #  if qf > 1: #TODO code should be correct. Implement as warduino side to process arguments
    #      #  dev.send_data(toAddr(dev, "DUMPLocals", hex(qf)))
    #      hx = hex(qf)[2:]
    #      _size = math.floor(len(hx) / 2)
    #      if _size % 2 != 0:
    #          print("WARNING: added O in front for qf\n")
    #          hx += '0'
    #          _size +=1

    #      _hex_siz = hex(_size)[2:]
    #      if _size < 16:
    #          _hex_siz = '0' + _hex_siz
    #      data += _hex_siz + hx

    data +='\n'
    dev.send_data(data.upper().encode('ascii'))

def update_fun(dev):
    dev.send_data(toAddr(dev, "UPDATEFun" ))

def update_local(dev):
    dev.send_data(toAddr(dev, "UPDATELocal" ))

