from abc import ABC, abstractmethod

class ASerial(ABC):

    @abstractmethod
    def run(self, state):
        raise NotImplementedError

    @abstractmethod
    def pause(self, state):
        raise NotImplementedError

    @abstractmethod
    def step(self, state):
        raise NotImplementedError

    @abstractmethod
    def add_breakpoint(self, state):
        raise NotImplementedError

    @abstractmethod
    def add_breakpoint(self, state):
        raise NotImplementedError

    @abstractmethod
    def halt(self, state):
        raise NotImplementedError

    @abstractmethod
    def initialize_step(self, state):
        raise NotImplementedError
