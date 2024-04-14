from math import floor

from core.Instrument import Coin
from marketmaker.RiskManager import RiskManager
from decimal import Decimal

class SkewByOffset:
    _maxSkew = 5
    def __init(self):
        pass
    @staticmethod
    def getBidSkew(coin: Coin):
        skew:Decimal = 0 if RiskManager.risks[coin].position > 0 else SkewByOffset._fraction(coin)
        return skew
    @staticmethod
    def getAskSkew(coin: Coin):
        skew: Decimal = 0 if RiskManager.risks[coin].position > 0 else SkewByOffset._fraction(coin)
        return skew
    @staticmethod
    def _fraction(coin):
        fraction: Decimal = min(RiskManager.risks[coin].position / RiskManager.riskLimits[coin],
                                1) * SkewByOffset._maxSkew
        return fraction