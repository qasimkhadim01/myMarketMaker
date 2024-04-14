import asyncio
import logging
from decimal import Decimal
from datetime import datetime

from Test.SimulatedExchange import SimulatedExchange
from connectivity.gateio.ws import Connection, Configuration
from marketmaker.SkewByOffset import SkewByOffset
from marketmaker.Strategy import Strategy
from math import floor

import Static
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from connectivity.gateio import Api
from core.Instrument import Instrument, Instruments, Coin
from core.MyEnums import OrderSide, Role
from core.Orders import FilledOrder, TickEvent, SpotMarketOrder
from marketmaker.MarketCache import MarketCache
from marketmaker.Risk import Risk

logger = logging.getLogger(__name__)


class RiskManager:
    riskLimits: {} = {}
    risks: {} = {}
    _pnlCoin: Coin = None
    _positionUpdateQueue: asyncio.Queue = None
    _totalVolume: Decimal = 0
    _exchangeManager: ExchangeManagerBase = None
    _skew: SkewByOffset = None

    def __init__(self, coins: {}, pnlCoin: Coin, exchangeManager: ExchangeManagerBase,
                 positionUpdateQueue: asyncio.Queue):
        RiskManager._positionUpdateQueue = positionUpdateQueue
        RiskManager._risks = {}
        RiskManager._pnlCoin = pnlCoin
        RiskManager._exchangeManager = exchangeManager
        [RiskManager._risks.update({coin: Risk(coin)}) for coin in coins]
        [RiskManager._riskLimits.update({coin: Strategy.RiskLimit.value}) for coin in coins]
        RiskManager._skew = SkewByOffset()

        if RiskManager._pnlCoin not in RiskManager._risks.keys():
            RiskManager._risks[pnlCoin] = Risk(pnlCoin)

    async def run(self):
        while True:
            result = await RiskManager._positionUpdateQueue.get()
            if isinstance(result, FilledOrder):
                self.onPositionUpdate(result)

    def onPositionUpdate(self, order: FilledOrder):
        midUsdPrice: Decimal = MarketCache.getMidPrice(order.instrument.base, abs(order.amount))
        usdAmt = abs(order.amount) * midUsdPrice

        RiskManager._totalVolume += usdAmt

        RiskManager._risks.get(order.instrument.base).processLeg(order)
        RiskManager._risks.get(order.instrument.counter).processLeg(order)
        logger.debug(f"onPositionUpdate completed {order}")

        RiskManager.isRiskLimitTriggered()

    @staticmethod
    def isRiskLimitTriggered():
        for coin in coins:
            if RiskManager._risks[coin].position > RiskManager._riskLimits[coin]:
                excess: Decimal = RiskManager._risks[coin].position - RiskManager._riskLimits[coin]
                excess += Decimal(0.1) * RiskManager._risks[coin].position
                marketOrder: SpotMarketOrder = SpotMarketOrder(RiskManager.nextOrderId(),
                                                               Instruments.instruments.get(Instrument(coin, Coin.USDT)),
                                                               OrderSide.Sell, Decimal(excess),
                                                               RiskManager._exchangeManager.localOrderBook.ob.bids[0])
                RiskManager._exchangeManager.sendMarketOrder(marketOrder)

    @staticmethod
    def skew(coin: Coin):
        bidSkew = RiskManager._skew.getBidSkew(coin)
        askSkew = RiskManager._skew.getAskSkew(coin)
        return bidSkew, askSkew

    @staticmethod
    def nextOrderId():
        orderId = "t-" + Api.subAccount + "_rm_" + str(Static.orderCounter)
        Static.orderCounter += 1
        return orderId



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

    exchangeManager = SimulatedExchange(instrument, conn)

    marketCache = MarketCache(coins, pnlCoin)
    rm: RiskManager = RiskManager(coins, pnlCoin, exchangeManager, queue)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(simulate())
    loop.create_task(rm.run())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()
