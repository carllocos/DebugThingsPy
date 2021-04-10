from communication import SerialConfig

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
            'exclusive': True,
            'fallback': '/dev/ttyUSB1'
        }
        return SerialConfig(**c)

    @staticmethod
    def socketConfig(dev=None, local=True):
        if local:
            return {'name': 'WARDuino'}
        else:
            return {}

    @staticmethod
    def serializer():
        return warduino.Serializer()

    @staticmethod
    def sockSerializer():
        return warduino_socket.Serializer()