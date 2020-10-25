
import interact
from devices_configs import esp32
import time

def start_dev(bp='0x47'):

    dev = interact.find_device(esp32.get_config())
    if dev:
        dev.connect()
        dev.enable_listening(verbose = True)
        interact.dump(dev)
        interact.run(dev)
        time.sleep(0.2)
        interact.add_bp(dev, bp)
        return dev
    else:
        print('no device found!')
        return False


def dump(dev):
    interact.dump(dev)

def dump_local(dev):
    interact.dump_local(dev)

def add_bp(dev, bp):
    interact.add_bp(dev, bp)

def remove_bp(dev, bp):
    interact.remove_bp(dev, bp)
def run(dev):
    interact.run(dev)
