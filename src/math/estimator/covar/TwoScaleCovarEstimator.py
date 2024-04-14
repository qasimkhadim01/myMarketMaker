import math

from src.estimator.LinearSynchronizer import LinearSynchronizer
from src.estimator.Sequencer import Sequencer
from src.timeseries.TimeSeries import TimeSeries


class TwoScaleCovarEstimaror:
    def __int__(self, halfWindow, samplingInterval):
        self.samplingInterval = samplingInterval
        self.slowSampleAdjustmentFactor = 1/(1-(1.0/self.samplingInterval))
        self.fastCovarEstimator = EmaSubSampleCovarEstimator(halfWindow, 1)
        self.slowCovarEstimator = EmaSubSampleCovarEstimator(halfWindow, 5)
        self.tickcount = 0
        self.warmUpTickCount = 20

    def initialize(self, timestamp, initialValue1, initialValue2):
        self.fastCovarEstimator.initialize(timestamp, initialValue1, initialValue2)
        self.slowCovarEstimator.initialize(timestamp, initialValue1, initialValue2)

    def update(self, timestamp, value1, value2):
        self.fastCovarEstimator.update(timestamp, value1, value2)
        self.slowCovarEstimator.update(timestamp, value1, value2)
        microStructureNoiseCorrection = self.fastCovarEstimator.covarPerDay/self.samplingInterval
        if math.abs(microStructureNoiseCorrection) < math.abs(self.slowSampleAdjustmentFactor):
            covariance = (self.slowSampleAdjustmentFactor *
                          ( self.slowCovarEstimator.covarPerDay - microStructureNoiseCorrection))
        else:
            covariance = self.slowCovarEstimator.covarPerDay

        if self.tickcount < self.warmUpTickCount:
            covariance = 0

        return covariance

    def compute(self, assetPrices):
        sequencer = Sequencer(assetPrices)
        linearSynchronizer = LinearSynchronizer()
        covars = TimeSeries("covars")
        while (sequencer.pop()):
            Side syncSide =  Side.Left if (sequencer.synchIndex ==0) else Side.Right
            linearSynchronizer.asyncUpdate(syncSide, sequencer.syncTime, sequencer.syncValue)
            if linearSynchronizer.isValid():
                self.update(linearSynchronizer,
                            math.log(linearSynchronizer.synchValues.getLeft(),
                            math.log(linearSynchronizer.synchValues.getRight)))
                covars.put(linearSynchronizer.synchTime, self.covariance)

        return covars

