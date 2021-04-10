def hex2Int(xStr):
    return int(xStr[2:], 16)

class Device:

    def __init__(self):
        super().__init__()
        self.__port_info = False
        self.__serial_config =False

    def __str__(self):
        return f'device={str(self.__port_info.device)}\tname={str(self.__port_info.name)}'

    def port_info(self, port_info):
        self.__port_info = port_info

    def serial_config(self, sc):
        self.__serial_config = sc

    def get_serial_config(self):
        return self.__serial_config
