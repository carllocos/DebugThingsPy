import json
from typing import Union
from twisted.internet import reactor

from utils import get_logger


ES_logger = get_logger("EventSystem")


Client = None


def change_client(c):
    global Client
    Client = c


class EventEmitter:
    def __init__(self, req):
        self.__req = req

    @property
    def req(self):
        return self.__req

    def emit(self, event_name, data=None):
        _content = {"event_name": event_name}
        if data is not None:
            _content["data"] = data
        json_str = json.dumps(_content)
        self.req.write(json_str.encode("utf-8"))

    def emitt_error(self, reason: str) -> None:
        json_str = '{"event_name":"error","reason":"' + reason + '"}'
        _bytes = json.dumps(json_str).encode("utf-8")
        self.req.write(_bytes)


class EventSystem:
    def __init__(self) -> None:
        self.__handlers = {}
        self.__client = None

    @property
    def client(self):
        return self.__client

    @client.setter
    def client(self, c):
        self.__client = c

    @property
    def logger(self):
        return ES_logger

    def data_receive(self, data: bytes, em: EventEmitter) -> None:
        event = self.__parse(data)
        if type(event) is str:
            em.emitt_error(event)
            return
        event_name = event["event_name"]
        event_data = event.get("data", event)
        self.handle_event(event_name, event_data, em)

    def on_event(self, event_name, cb) -> None:
        ES_logger.debug(f"add cb for event `{event_name}`")
        self.__handlers[event_name] = cb

    def on_disconnection(self) -> None:
        change_client(None)
        event_name = "disconnection"
        cb = self.__handlers.get(event_name, self.__handlers.get("*", None))
        if cb is not None:
            cb()
        else:
            ES_logger.error(f"found unhandled event `{event_name}`")

    def handle_event(self, event_name: str, data, emitter: EventEmitter) -> None:
        cb = self.__handlers.get(event_name, self.__handlers.get("*", None))
        if cb is not None:
            cb(data, emitter)
        else:
            ES_logger.error(f"found unhandled event `{event_name}` data `{data}`")

    def emit(self, event_name, data=None):
        reactor.callFromThread(self.__emit_thread, event_name, data)

    def __emit_thread(self, event_name, data=None):
        global Client
        _content = {"event_name": event_name}
        if data is not None:
            _content["data"] = data
        json_str = json.dumps(_content)
        if Client is not None:
            Client.write(json_str.encode("utf-8"))
        else:
            ES_logger.error("emitting while no emitter set")

    def __parse(self, data: bytes) -> Union[dict, str]:
        ES_logger.debug(f"parsing {data}")
        try:
            _event = json.loads(data.decode("utf-8"))
            try:
                _event["event_name"]
                return _event
            except KeyError:
                ES_logger.error("JSON missing `event_name` key")
                return "missing `event_name` key"
        except UnicodeDecodeError:
            ES_logger.error("could not decode")
            return "Unicode decode error"
        except json.decoder.JSONDecodeError:
            ES_logger.error("could not parse JSON")
            return "Could not parse JSON"
