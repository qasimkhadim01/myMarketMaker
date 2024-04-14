from abc import ABC, abstractmethod


class ICovarEstimator(ABC):
    @abstractmethod
    def update(self, timestamp, value1, value2):
        pass
