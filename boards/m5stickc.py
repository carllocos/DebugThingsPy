from communication import serial as ser
from . import warduino

class M5StickC:


    @staticmethod
    def serialConfig(dev=None):
        dev = '/dev/ttyUSB0' if dev is None else dev
        c = {
            'name': 'ttyUSB0',
            'device': dev,
            'baudrate': 115200,
            'timeout': float(5),
            'write_timeout': float(5),
            'exclusive': True
        }
        return ser.SerialConfig(**c)


    @staticmethod
    def serializer():
        return warduino.Serializer()
