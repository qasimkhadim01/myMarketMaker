from math.estimator.volatility.EmaSubSampleVarEstimatorNew import EmaSubSampleVarEstimatorNew
from math.estimator.volatility.HighFrequencyVarEstimatorBase import HighFrequencyVarEstimatorBase


class HighFrequencyVarEstimator(HighFrequencyVarEstimatorBase):
    def __init__(self, halfLife, samplingInterval):
        super().__init__(halfLife, samplingInterval)
        self.fastVarEstimator = EmaSubSampleVarEstimatorNew(halfLife, 1)
        self.slowVarEstimator = EmaSubSampleVarEstimatorNew(halfLife, samplingInterval)