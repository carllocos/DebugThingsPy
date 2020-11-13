from enum import Enum

class CBState(Enum):
    OPEN = 1
    CLOSED = 2
    HALF_OPEN = 3


class ReqCircuitBreaker:
    #implementation of the circuit breaker

    def __init__(self, req, options = {}):
        super().__init__()
        self.__state =CBState.CLOSED
        self.__request = req
        self.__options = options


    def state(self):
        return self.__state

    def trip(self):
        self.__state = CBState.OPEN

    def reset(self):
        self.__state = CBState.CLOSED

    def attempt_reset(self):
        self.__state = CBState.HALF_OPEN

    def on_closed(self, cb):
        pass

    def send(self):
        if self.__state != CBState.CLOSED:
            return False
        self.__request.send()
