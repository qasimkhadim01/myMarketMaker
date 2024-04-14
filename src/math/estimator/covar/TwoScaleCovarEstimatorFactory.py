from estimator.covar.ICovarEstFactory import ICovarEstFactory


class TwoScaleCovarEstimatorFactory(ICovarEstFactory):
    def __init__(self, halfWindow, samplingInterval):
        self.halfWindow = halfWindow
        self.samplingInterval = samplingInterval

    def build(self):
        return Two