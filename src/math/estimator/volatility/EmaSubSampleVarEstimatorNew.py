from src.core import TimeHelper
from src.estimator.volatility.EmaSubSampleVarEstimatorBase import EmaSubSampleVarEstimatorBase


class EmaSubSampleVarEstimatorNew(EmaSubSampleVarEstimatorBase):
    def __init__(self, halfWindow, samplingInterval):
        super().__init__(halfWindow, samplingInterval)
        self.count = 0

    def updateVarRateEst(self, timestamp, value):
        logPrice = value

        if self.count == 0:
            self.initialize(timestamp, value)
        self.count = 1
        historyIndex = self.count % self.samplingInterval
        change = logPrice - self.samplingInterval
        changeTime = (timestamp - self.timeSampleHistory[historyIndex]).total_seconds()/TimeHelper.SecondsInDay
        variation = change * change

        if changeTime > 0:
            normalisedVariation = variation / changeTime
            self.tickIntervalEma = self.decayFactor * self.tickIntervalEma+(1-self.decayFactor)*changeTime
            self.emaEstimate = self.decayFactor * self.emaEstimate + (1-self.decayFactor) * normalisedVariation
            self.varPerTick = self.emaEstimate

            self.valueHistory[historyIndex] = value
            self.timeSampleHistory[historyIndex] = timestamp
            if self.tickIntervalEma > 0 :
                self.varPerDay = self.emaEstimate

        return self.varPerDay