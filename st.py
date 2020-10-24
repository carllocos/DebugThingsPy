
import interact
from devices_configs import esp32
import time

def start_dev():

    dev = interact.find_device(esp32.get_config())
    if dev:
        dev.connect()
        dev.enable_listening(verbose = True)
        interact.dump(dev)
        interact.run(dev)
        return dev
    else:
        print('no device found!')
        return False


def bp(s=''):
    #  digWriteCall = '000007d'
    digWriteCall = '0x7D'
    if s == 'callDigWrite':
        return digWriteCall
    else:
       return digWriteCall
