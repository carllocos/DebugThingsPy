import threading
import serial
from serial.tools import list_ports

class Device:

    def __init__(self, list_port_info):
        super().__init__()
        self.__lpi = list_port_info
        self.__serial = False
        self.__config = None
        self.__serial = None
        self.__recvs = []
        self.__listener = None
        self.__verbose = False

    def __str__(self):
        return f'device={str(self.__lpi.device)}\tname={str(self.__lpi.name)}'

    def set_config(self, c):
        self.__config = c

    def connect(self, device_config=None):
        if device_config is None and self.__config is None: #TODO remove device_config
            raise TypeError("device config argument missing")

        self.close() #close any connection if needed

        b = self.__config.baudrate
        rt = self.__config.timeout
        wt = self.__config.write_timeout
        bs = serial.EIGHTBITS
        #  ex = self.__config.exclusive
        #  self.__serial = serial.serial_for_url(self.__lpi.device, baudrate=b, timeout=rt, write_timeout=wt, bytesize=bs)#, exclusive=ex)
        self.__serial = serial.Serial(self.__lpi.device, baudrate=b, timeout=rt, write_timeout=wt, bytesize=bs)#, exclusive=ex)
        return True

    def close(self):
        if self.__serial is not None:
            self.__serial.close()

    def list_port_info(self):
        return self.__lpi

    def get_serial(self):
        return self.__serial

    def enable_listening(self, verbose = False):
        if self.__serial is None:
            raise TypeError('connect first, invoke method connect on device')
        if self.__listener is None:
            print(f'creating the thread! verbose {verbose}')
            self.__listener = threading.Thread(target=read_data, args=(self,))
            self.__verbose = verbose
            self.__listener.start()

    def append_msg(self, m):
        self.__recvs.append(m)

    def send_data(self, data_bytes):
        a = self.__serial.write(data_bytes)
        print(f"total bytes send {a}")

    def is_verbose(self):
        return self.__verbose

def read_data(dev):
    __to_ignore = ["chip_delay", "digital_write", "no interrupt"]
    __all_msgs = set()
    while True:
        b = dev.get_serial().read_until(bytes([ord('\n')]))
        msg = b.decode('utf-8')
        print(msg)
