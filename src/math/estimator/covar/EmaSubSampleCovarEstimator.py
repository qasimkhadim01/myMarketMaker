import math

import numpy as np

from src.timeseries.TimeSeries import TimeSeries


class EmaSubSampleCovarEstimator(EmaEstimator):
    def __int__(self, halfWindow, samplingInterval):
        super.__init__(halfWindow)
        self.samplingInterval = samplingInterval
        self.valueHistory1 = np.arange(samplingInterval)
        self.valueHistory2 = np.arange(samplingInterval)
        self.timeStampHistory = np.arange(samplingInterval)

    def getCovarPerDay(self):
        return self.getCovarPerDay

    def initialize(self, timestamp, initialValue1, initialValue2):
        for i in range(self.samplingInterval):
            self.timeStampHistory[i] = timestamp
            self.valueHistory1 = initialValue1
            self.valueHistory2 = initialValue2

    def update(self, timestamp, value1, value2):
        self.initialize(timestamp, value1, value2) if self.count == 0 else None
        self.count = self.count + 1
        historyIndex = self.count % self.samplingInterval
        change1 = value1 - self.valueHistory1[historyIndex]
        change2 = value2 - self.valueHistory2[historyIndex]
        changeTime = (self.timeStampHistory[historyIndex] - timestamp).astype(np.int64)
        covariation = change1 * change2
        self.tickIntervalEma = self.decayFactor * self.tickIntervalEma + (1 - self.decayFactor) * changeTime
        self.emaEstimate = self.decayFactor * self.emaEstimate + (1 - self.decayFactor) * covariation
        self.valueHistory1[historyIndex] = value1
        self.valueHistory2[historyIndex] = value2
        self.timeStampHistory[historyIndex] = timestamp
        covarPerDay = 0
        if self.tickIntervalEma > 0:
            covarPerDay = self.emaEstimate / self.tickIntervalEma

    def compute(self, assetPrices):
        covars = TimeSeries("covar")
        for key, value in assetPrices.getLeft().items():
            timestamp = key
            val1 = value
            val2 = assetPrices.getRight()[key]
            self.update(timestamp, math.log(val1), math.log(val2))
            covars.put(timestamp, self.covarPerDay)
