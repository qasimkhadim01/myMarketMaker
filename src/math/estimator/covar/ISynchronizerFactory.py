from abc import ABC, abstractmethod

class ISynchronizerFactory(ABC):
    @abstractmethod
    def build(self):
        pass