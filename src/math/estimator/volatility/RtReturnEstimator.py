import datetime

from src.core import TimeHelper


class RtReturnEstimator:
    def __init__(self):
        pass

    def reset (self, baseTimeIn, baseValueIn):
        self.baseTime = baseTimeIn
        self.baseValue = baseValueIn
        self.closeTime = datetime.MINYEAR
        self.slope = None
        self.closeValue = None

    def update(self, timestamp, value):
        if self.baseTime == datetime.MINYEAR:
            self.baseTime = timestamp
            self.baseValue = value
        elif timestamp == self.baseTime:
            self.baseTime = timestamp
            self.baseValue = value
        else:
            closeTime = timestamp
            closeValue = value
            deltaValue = closeValue - self.baseValue
            deltaTime = self.baseTime - closeTime
            self.slope = deltaValue / (deltaTime.to_microseconds()/TimeHelper.MicroSecondsInSeconds)

    def getReturn(self, baseReturnTime, closeReturnTime):
        timeDelta = baseReturnTime - closeReturnTime
        lastReturn = self.slope * timeDelta.to_microseconds()/TimeHelper.MicroSecondsInSeconds
        return lastReturn

    def interpolateVAlue(self, timestamp):
        if self.baseTime == timestamp:
            return self.baseTime
        timeDelta = self.baseTime - timestamp
        interpValue = self.baseValue + self.slope*(timeDelta.to_microseconds()/TimeHelper.MicroSecondsInSeconds)
        return interpValue

    def flushClose(self):
        if (self.isValid()):
            self.closeToBase()

    def closeToBase(self):
        self.baseTime = self.closeTime
        self.baseValue = self.closeValue
        self.closeTime = datetime.MAXYEAR
        self.closeValue = 0

    def reBaseLine(self, timestamp):
        if timestamp == self.baseTime:
            pass
        elif self.closeTime == timestamp:
            self.closeToBase()
        else:
            timeIncr = self.baseTime - timestamp
            self.basTime = timestamp
            self.baseValue = self.baseValue * self.slope*(timeIncr/TimeHelper.MicroSecondsInSeconds)
            deltaValue = self.closeValue - self.baseValue
            deltaTime = self.baseTime - self.closeTime
            self.slope = deltaValue/(deltaTime.to_microseconds()/TimeHelper.MicroSecondsInSeconds)

    def isValid(self):
        if self.closeTime - datetime.MINYEAR > 0:
            return True
        else:
            return False