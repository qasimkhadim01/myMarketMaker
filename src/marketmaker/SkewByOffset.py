import logging

from numpy import sign

from math import floor

from core.Instrument import Coin
from decimal import Decimal

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class SkewByOffset:
    _maxSkew = 4
    skewMidFactor = Decimal(0.3)
    def __init(self):
        pass

    @staticmethod
    def getBidSkew(coin: Coin, position: Decimal, riskLimit):
        skew: Decimal = SkewByOffset._fraction(coin, position, riskLimit) if position > 0 else 0
        return skew

    @staticmethod
    def getAskSkew(coin: Coin, position, riskLimit):
        skew: Decimal = SkewByOffset._fraction(coin, position, riskLimit) if position < 0 else 0
        return skew

    @staticmethod
    def _fraction(coin, position, riskLimit):
        fraction: Decimal = min((abs(position) / riskLimit), 1)
        return fraction
    @staticmethod
    def getMidSkew(coin: Coin, position, riskLimit):
        skew: Decimal = abs(position) / riskLimit
        skew = skew * sign(position)
        return skew
