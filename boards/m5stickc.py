from communication import serial as ser
from . import warduino

class M5StickC:


    @staticmethod
    def serialConfig():
        c = {
            'name': 'ttyUSB0',
            'device': '/dev/ttyUSB0',
            'baudrate': 115200,
            'timeout': float(5),
            'write_timeout': float(5),
            'exclusive': True
        }
        return ser.SerialConfig(**c)


    @staticmethod
    def serializer():
        return warduino.Serializer()
