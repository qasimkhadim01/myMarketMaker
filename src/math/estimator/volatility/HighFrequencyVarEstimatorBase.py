import numpy as np

class HighFrequencyVarEstimatorBase:
    def __init__(self, halfLife, samplingInterval):
        self.samplingInterval = samplingInterval
        self.slowSamplingAdjustmentFactor = 1/(1-(1.0/samplingInterval))
        self.fastVarEstimator = None
        self.slowVarEstimator = None
        self.tsVar = None

    def initialize(self, timestamp, initialValue):
        self.fastVarEstimator(timestamp, initialValue)
        self.slowVarEstimator(timestamp, initialValue)
        self.tsVar = 0

    def updateVarEst(self, timestamp, value):
        logPrice = value
        self.fastVarEstimator.updateVarRateEst(timestamp, logPrice)
        self.slowVarEstimator.updateVarRateEst(timestamp, logPrice)
        self.tsVar = (self.slowSamplingAdjustmentFactor
                      *(self.slowVarEstimator.varPerDay - self.fastVarEstimator.varPerDay/self.samplingInterval))
        self.tsVarPerTick = (self.slowSamplingAdjustmentFactor
                             * (self.slowVarEstimator.varPerTick-self.fastVarEstimator.varPerTick/self.samplingInterval))

        if self.tsVar < 0:
            self.tsVar = self.slowVarEstimator.varPerDay

        return self.getTsrVol()

    def getFastVol(self):
        return np.sqrt(np.max(self.fastVarEstimator.getVarPerDay(),0))

    def getSlowVol(self):
        return np.sqrt(np.max(self.slowVarEstimator.getVarPerDay(),0))
    def getFastVolPerTick(self):
        return np.sqrt(np.max(self.fastVarEstimator.getVarPerTick(),0))
    def getSlowVolPerTick(self):
        return np.sqrt(np.max(self.slowVarEstimator.getVarPerTick(),0))

    def getTsrVol(self):
        if (self.tsVar >0 ):
            tsrVol = np.sqrt(self.tsVar)
        else:
            tsrVol = 0
        return tsrVol

    def realizedVol(self, assetPrices):
        ts = TimeSeries("vols")
        for idx, row in assetPrices.df.iterrows():
            self.updateVarEst(row.timestamp, np.log(row.value))
            ts.add(row.timestamp, self.getTsrVol())

        return ts