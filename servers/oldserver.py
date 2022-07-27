from __future__ import annotations
import socketserver
import json

from utils import get_logger
from eventsystem import EventSystem, EventEmitter

logger = get_logger("ClientSocketServer")


class MyTCPServer(socketserver.TCPServer):
    def handle_error(self, request, client_address):
        logger.error(f"Some error occorred {request}")
        super().handle_error(request, client_address)


class RequestHandler(socketserver.StreamRequestHandler):
    allow_reuse_address = True
    EventHandlers = EventSystem()
    EventBuffer = b""

    def handle(self) -> None:
        global EventBuffer
        RequestHandler.EventBuffer += self.request.recv(1024).strip()
        self.data = RequestHandler.EventBuffer
        logger.info(f"got from {self.client_address[0]} as data {self.data}")

        if self.data == b"":
            return

        try:
            _event = json.loads(self.data.decode())
            RequestHandler.EventBuffer = b""
            RequestHandler.EventHandlers.handle_event(
                _event.get("event_name", None),
                _event.get("data", _event),
                EventEmitter(self.request),
            )
        except json.decoder.JSONDecodeError:
            logger.info("could not parse JSON")

    def finish(self) -> None:
        logger.info("cleaning up the request")
        return super().finish()

    @staticmethod
    def set_event_handlers(event_handlers):
        RequestHandler.EventHandlers = event_handlers


def run_server(host_port, event_handlers):
    # with socketserver.TCPServer(host_port, RequestHandler) as server:
    with MyTCPServer(host_port, RequestHandler) as server:
        RequestHandler.set_event_handlers(event_handlers)
        server.serve_forever()
