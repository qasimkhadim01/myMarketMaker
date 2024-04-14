import numpy as np
from abc import ABC, abstractmethod
from src.estimator.EmaEstimator import EmaEstimator


class EmaSubSampleVarEstimatorBase(ABC, EmaEstimator):
    def __init__(self, halfWindow, samplingInterval):
        super().__init__(halfWindow)
        self.samplingInterval = samplingInterval
        self.valueHistory = np.empty(samplingInterval)
        self.timeSampleHistory = np.empty(samplingInterval).astype("datetime64[ns]")
        self.tickIntervalEma =0
        self.emaEstimate = 0
        self.varPerDay = 0
        self.varPerTick = 0

    def initialize(self, timestamp, initialValue):
        for i in range(0, self.samplingInterval):
            self.timeSampleHistory[i] = timestamp
            self.valueHistory[i] = initialValue

    @abstractmethod
    def updateVarRateEst(self, timestamp, value):
        pass