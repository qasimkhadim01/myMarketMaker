import asyncio
import logging
from decimal import Decimal
from datetime import datetime

from numpy import sign

import Static
import math
from connectivity import LocalOrderBookBase
from connectivity.gateio.ws import Connection, Configuration
from marketmaker.SkewByOffset import SkewByOffset
from marketmaker.Strategy import Strategy, RiskParam
from connectivity.gateio import Api
from core.Instrument import Instrument, Instruments, Coin
from core.MyEnums import OrderSide, Role
from core.Orders import FilledOrder, TickEvent, SpotMarketOrder
from marketmaker.MarketCache import MarketCache

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Risk:
    def __init__(self, coin: Coin):
        self.coin = coin
        self.position: Decimal = Decimal(0)
        self.positionValue: Decimal = Decimal(0.0)
        self.meanHoldingTime = 0
        self.costBasis = 0

    def processLeg(self, order: FilledOrder):
        signedAmount: Decimal = order.getSignedAmount() if order.instrument.base == self.coin else order.getQuoteSignedAmount()
        coinMarketPrice = RiskManager.localOrderBooks[self.coin].ob.bids[0].price

        exAntePosition: Decimal = self.position
        self.position = self.position + signedAmount
        self.positionValue = self.position * coinMarketPrice

        if (exAntePosition == 0) or (sign(signedAmount) == sign(exAntePosition)):
            costBasisChange = signedAmount * coinMarketPrice
        elif math.fabs(signedAmount) <= math.fabs(exAntePosition):
            reductionFraction: Decimal = abs(signedAmount) / abs(exAntePosition)
            costBasisChange = -self.costBasis * reductionFraction
        else:
            costBasisChange = self.position * coinMarketPrice - self.costBasis

        self.costBasis += costBasisChange

class RiskManager:
    riskLimits: {} = {}
    risks: {} = {}
    _pnlCoin: Coin = None
    _positionUpdateQueue: asyncio.Queue = None
    _totalVolume: Decimal = 0
    _skew: SkewByOffset = None
    localOrderBooks: dict[Coin, LocalOrderBookBase] = dict[Coin, LocalOrderBookBase]

    def __init__(self, coins: {}, pnlCoin: Coin, localOrderBooks: dict[Coin, LocalOrderBookBase]):
        # RiskManager._positionUpdateQueue = positionUpdateQueue
        RiskManager.risks = {}
        RiskManager._pnlCoin = pnlCoin
        [RiskManager.risks.update({coin: Risk(coin)}) for coin in coins]
        [RiskManager.riskLimits.update({coin: RiskParam.RiskLimit.value}) for coin in coins]
        RiskManager._skew = SkewByOffset()
        RiskManager.localOrderBooks = localOrderBooks
        if RiskManager._pnlCoin not in RiskManager.risks.keys():
            RiskManager.risks[pnlCoin] = Risk(pnlCoin)

    async def run(self):
        while Static.KeepRunning:
            result = await RiskManager._positionUpdateQueue.get()
            if isinstance(result, FilledOrder):
                self.onPositionUpdate(result)
        logging.error("Kill Switch Triggered")

    @staticmethod
    def onPositionUpdate(order: FilledOrder):
        midUsdTPrice: Decimal = RiskManager.localOrderBooks[order.instrument.base].ob.bids[0].price
        usdtAmt = abs(order.amount) * midUsdTPrice

        RiskManager._totalVolume += usdtAmt

        RiskManager.risks.get(order.instrument.base).processLeg(order)
        RiskManager.risks.get(order.instrument.counter).processLeg(order)
        logger.debug(f"{order}")

    @staticmethod
    def skewByOffset(coin: Coin):
        bidSkew = RiskManager._skew.getBidSkew(coin, RiskManager.risks[coin].positionValue, RiskManager.riskLimits[coin])
        askSkew = RiskManager._skew.getAskSkew(coin, RiskManager.risks[coin].positionValue, RiskManager.riskLimits[coin])
        return bidSkew, askSkew

    def midSkew(coin: Coin):
        return RiskManager._skew.getMidSkew(coin, RiskManager.risks[coin].positionValue, RiskManager.riskLimits[coin])

    @staticmethod
    def realizedPnl():
        realizedPnl = 0
        for key, value in RiskManager.risks.items():
            realizedPnl += value.costBasis
        return realizedPnl

    @staticmethod
    def unRealizedPnl():
        unrealizedPnl = 0
        for key, value in RiskManager.risks.items():
            rate = RiskManager.localOrderBooks[key].midTob
            if key != RiskManager._pnlCoin:
                unrealizedPnl += value.position * rate - value.costBasis

        return unrealizedPnl
async def simulate():
    instrument = Instruments.instruments["UMEE_USDT"]

    event1: TickEvent = TickEvent(datetime.now(), instrument, Decimal(1.1), Decimal(1.2))
    order1: FilledOrder = FilledOrder("orderId1", instrument, OrderSide.Buy, Decimal(1000), Decimal(1.1), Role.Maker)
    MarketCache.onTickEvent(event1)
    await queue.put(order1)

    order2: FilledOrder = FilledOrder("orderId2", instrument, OrderSide.Buy, Decimal(1000), Decimal(1.4), Role.Maker)
    await queue.put(order2)

    event2: TickEvent = TickEvent(datetime.now(), instrument, Decimal(1.5), Decimal(1.6))
    MarketCache.onTickEvent(event2)

    # order3: FilledOrder = FilledOrder("orderId3", instrument, OrderSide.Buy, Decimal(1000), Decimal(1.4), Role.Maker)
    # await queue.put(order3)

    event3: TickEvent = TickEvent(datetime.now(), instrument, Decimal(1.8), Decimal(1.9))
    MarketCache.onTickEvent(event3)


if __name__ == "__main__":
    pnlCoin = Coin.USDT
    coins = [Coin.UX]
    queue: asyncio.Queue = asyncio.Queue()
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    instrument = "BTC_USDT"

    marketCache = MarketCache(coins, pnlCoin)
    rm: RiskManager = RiskManager(coins, pnlCoin, queue)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(simulate())
    loop.create_task(rm.run())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()
