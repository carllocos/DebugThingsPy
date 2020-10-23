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

def toByte(interupt_type, d=''):
    r = INTERUPT_TYPE[interupt_type] + d + '\n'
    return r.encode('ascii')

def run(dev):
    dev.send_data(toByte( "RUN" ))

def halt(dev):
    dev.send_data(toByte( "HALT" ))

def pause(dev):
    dev.send_data(toByte( "PAUSE" ))

def step(dev):
    dev.send_data(toByte( "STEP" ))

def add_bp(dev, bp):
    dev.send_data(toByte( "BPAdd", bp ))

def remove_bp(dev, bp):
    dev.send_data(toByte( "BPRem", bp ))

def dump(dev):
    dev.send_data(toByte( "DUMP" ))

def dump_local(dev):
    dev.send_data(toByte( "DUMPLocals" ))

def update_fun(dev):
    dev.send_data(toByte( "UPDATEFun" ))

def update_local(dev):
    dev.send_data(toByte( "UPDATELocal" ))

