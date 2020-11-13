from abc import ABC
from enum import Enum

class MsgState(Enum):
    IDLE = 0
    SEND = 1
    DONE = 2
    WAITING = 3


class Request(ABC):
    REQUEST_ID = 0

    def __init__(self, message):
        super().__init__()

        self.__id = Request.REQUEST_ID
        Request.REQUEST_ID += 1

        self.message = message
        self.state = MsgState.IDLE

    def mark_send(self):
        self.state = MsgState.SEND

    def mark_done(self):
        self.state = MsgState.DONE

    def mark_waiting(self):
        self.state = MsgState.WAITING

    #  @staticmethod
    #  def wrap_with_cb(protocol, payload, serializer, options = {}):
    #      req = Request(protocol, payload, serializer)
    #      return circuit_breaker.ReqCircuitBreaker(req, options)


