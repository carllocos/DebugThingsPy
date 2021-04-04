from abc import ABC, abstractmethod

class Medium(ABC):

    @abstractmethod
    def start_connection(self, dev):
        raise NotImplementedError

    @abstractmethod
    def close_connection(self, dev):
        raise NotImplementedError

    @abstractmethod
    def send(self, message, dev):
        raise NotImplementedError

    @abstractmethod
    def discover_devices(self):
        raise NotImplementedError

