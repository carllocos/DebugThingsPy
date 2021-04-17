from __future__ import annotations
from typing import Union, Any

from interfaces import ASerial
from boards import M5StickC
from communication import Sockets, MCUSerial
from boards import WARDuino

class Device(WARDuino):

    def __init__(self, config: dict) -> Device:
        super().__init__()
        self.__name = config['name']
        self.__remote = None
        self.__socket = None
        self.__serial = None
        self.__debugger = None
        self.__host = None
        self.__port = None

        if config.get('port', False):
            p = config['port']
            h = config.get('host', 'localhost')
            self.__socket = Sockets(p, h)
            self.medium = self.__socket
            self.__host = self.medium.host
            self.__port = self.medium.port

        elif config.get('serial', False):
            c = M5StickC.serialConfig(config['serial'])
            self.__serial = MCUSerial(c)
            self.medium = self.__socket

        if None not in [self.__socket, self.__serial]:
            self.redirect_dbg(self.__serial)

        if self.__serial is not None:
            self.__remote = True
        elif self.__socket is not None:
            if self.__socket.host == 'localhost':
                self.__remote  = False
            else:
                self.__remote = True
        else:
            self.__remote = False

    @property
    def name(self) -> str:
        return self.__name

    @property
    def socket(self) -> Union[Sockets, None]:
        return self.__socket

    @property
    def serial(self) -> Union[MCUSerial, None]:
        return self.__serial

    @property
    def is_remote(self) -> bool:
        return self.__remote

    @property
    def is_local(self) -> bool:
        return not self.__remote

    @property
    def uses_serial(self) -> bool:
        return self.__serial is  not None

    @property
    def uses_socket(self) -> bool:
        return self.__socket is not None

    @property
    def debugger(self) -> Any:
        return self.__debugger

    @debugger.setter
    def debugger(self, _dbg) -> None:
        self.__debugger = _dbg
        self.set_debugger(_dbg)

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> str:
        return self.__port