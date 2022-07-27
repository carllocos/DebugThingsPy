from __future__ import annotations
from typing import Union

from twisted.internet.protocol import Factory
from twisted.internet import reactor

from utils import get_logger

ServerLogger = get_logger("TCPServer")


class TCPServer:
    def __init__(self, port: int = 8167):
        self.port = port

    def run(self, protocol):
        f = Factory()
        f.protocol = protocol
        ServerLogger.info(f"starting {self.port}")
        reactor.listenTCP(self.port, f)
        reactor.run()
