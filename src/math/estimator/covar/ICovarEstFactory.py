from abc import ABC, abstractmethod

class ICovarEstFactory(ABC):
    @abstractmethod
    def build(self):
        pass