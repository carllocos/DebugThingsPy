from __future__ import annotations
from boards import Device

#TODO move to Device
def load_device(config: dict) -> Device:
    return Device(config)
