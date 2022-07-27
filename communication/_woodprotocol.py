from __future__ import annotations
from twisted.internet.protocol import Protocol
from twisted.python import failure

from utils import get_logger
from eventsystem import EventSystem, EventEmitter, change_client


class WOODProtocol(Protocol):

    event_system = EventSystem()
    logger = get_logger("WOODProtocol")

    def connectionMade(self):
        super().connectionMade()
        WOODProtocol.logger.info("connection established")
        change_client(self.transport)

    def connectionLost(self, reason: failure.Failure = ...):
        WOODProtocol.logger.info("connection lost")
        WOODProtocol.event_system.on_disconnection()
        return super().connectionLost(reason)

    def dataReceived(self, data):
        em = EventEmitter(self.transport)
        WOODProtocol.event_system.data_receive(data, em)

    @staticmethod
    def update_eventsystem(es: EventSystem):
        WOODProtocol.event_system = es
