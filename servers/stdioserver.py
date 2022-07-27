from __future__ import annotations
from typing import Union

# import sys
import json

from twisted.protocols import basic
from twisted.internet import reactor, stdio
from twisted.python import failure

from utils import get_logger

# from eventsystem import EventSystem, EventEmitter

ServerLogger = get_logger("StdIOServer")


def error_json(reason: str) -> bytes:
    json_str = '{"event_name":"error","reason":"{reason}"}'
    return json.dumps(json_str).encode("utf-8")


class WOODProtocol(basic.LineReceiver):
    delimiter = b"\n"

    def connectionMade(self):
        super().connectionMade()
        ServerLogger.info("connection established")

    def connectionLost(self, reason: failure.Failure = ...):
        ServerLogger.info("connection lost")
        return super().connectionLost(reason)

    def lineReceived(self, line):
        event = self.__parse_line(line)
        if event is None:
            _bytes = error_json("expecting JSON")
            self.transport.write(_bytes)
            return
        elif event.get("event_name") is None:
            _bytes = error_json('missing "event_name" key')
            self.transport.write(_bytes)
            return

        event_name = event["event_name"]
        answer = f"got event {event_name}"
        self.transport.write(answer.encode("utf-8"))

    def __parse_line(self, line: str) -> None:
        ServerLogger.info(f"parsing {line}")
        try:
            _event = json.loads(line)
            try:
                _event["event_name"]
            except KeyError:
                ServerLogger.error("JSON missing `event_name` key")
            return _event
        except json.decoder.JSONDecodeError:
            ServerLogger.error("could not parse JSON")


class StdIOServer:
    def run(self, protocol: Union[WOODProtocol, None] = None):
        protocol = WOODProtocol() if protocol is None else protocol
        ServerLogger.info("Starting StdIO Server")
        stdio.StandardIO(protocol)
        reactor.run()


# class StdIOServer:
#     def __init__(self, event_system: EventSystem):
#         self.__eventsys = event_system

#     def parse_line(self, line: str) -> None:
#         logger.info(f"got {line}")
#         try:
#             _event = json.loads(line)
#             print(f"got event {_event['event_name']}")
#             self.__eventsys.handle_event(
#                 _event["event_name"], EventEmitter(_event["data"])
#             )
#         except json.decoder.JSONDecodeError:
#             logger.info("could not parse JSON")

#     def run(self):
#         for line in sys.stdin:
#             self.parse_line(line)
