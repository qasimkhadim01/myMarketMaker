import logging

from numpy import sign

import math
from decimal import Decimal

from core.Instrument import Coin
from core.Orders import FilledOrder
from marketmaker.MarketCache import MarketCache
from marketmaker.RiskManager import RiskManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Static.appLoggers.append(logger)

class Risk:
    def __init__(self, coin: Coin):
        self.coin = coin
        self.position: Decimal = 0
        self.meanHoldingTime = 0
        self.costBasis = 0

    def processLeg(self, order: FilledOrder):
        signedAmount: Decimal = order.getSignedAmount() if order.instrument.base == self.coin else order.getQuoteSignedAmount()
        coinMarketPrice = RiskManager.localOrderBooks[self.coin]

        exAntePosition: Decimal = self.position
        self.position += signedAmount

        if (exAntePosition == 0) or (sign(signedAmount) == sign(exAntePosition)):
            costBasisChange = signedAmount * coinMarketPrice
        elif math.fabs(signedAmount) <= math.fabs(exAntePosition):
            reductionFraction: Decimal = abs(signedAmount) / abs(exAntePosition)
            costBasisChange = -self.costBasis * reductionFraction
        else:
            costBasisChange = self.position * coinMarketPrice - self.costBasis

        self.costBasis += costBasisChange
