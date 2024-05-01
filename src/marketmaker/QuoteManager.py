import asyncio
import copy
import random

from connectivity.gateio.LocalOrderBook import OrderBookEntry
from math import floor
from typing import List
import time

import Static
from connectivity.gateio import Api
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Instruments, Instrument, Coin
from core.Orders import SpotLimitOrder, SpotMarketOrder, FilledOrder, Order
from core.MyEnums import OrderSide, OrderStatus
from marketmaker.RiskManager import RiskManager
from marketmaker.SkewByOffset import SkewByOffset
from marketmaker.Strategy import Strategy, OrderSizeInDollar, liveStrategies, DefensiveStrategy, TOUCHED, Touched, \
    MultiRandomStrategy, MultiLadderStrategy, JoinStrategy, BestStrategy
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QuoteManager:
    def __init__(self, instrument: Instrument, exchangeManager: ExchangeManagerBase):
        self.instrument = instrument
        self.exchangeManager = exchangeManager
        self.myBids = {}
        self.myAsks = {}
        self.myMarketOrders: dict[str, SpotMarketOrder] = dict()
        self.executedOrders: List[Order] = list()
        self.waitingForMarketOrders = False

    def release(self):
        self.exchangeManager.release()
        # cancel all quootes
        [self.exchangeManager.cancelLimitOrder(order) for order in self.myBids.values()]
        self.myBids.clear()
        [self.exchangeManager.cancelLimitOrder(order) for order in self.myAsks.values()]
        self.myAsks.clear()


    def initialize(self):
        if len(self.exchangeManager.localOrderBook.bids) > 0:
            for strategy in liveStrategies:
                bidPrices, askPrices = self.buildStrategy(strategy)
                for bidPrice in bidPrices:
                    bidOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), self.instrument, OrderSide.Buy
                                                          , OrderSizeInDollar.sizes[0] / bidPrice,
                                                          bidPrice, strategy)
                    self.myBids.update({bidOrder.id: bidOrder})
                for askPrice in askPrices:
                    askOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), self.instrument, OrderSide.Sell
                                                          , OrderSizeInDollar.sizes[0] / askPrice,
                                                          askPrice, strategy)


                    self.myAsks.update({askOrder.id: askOrder})

            newOrders:List[SpotLimitOrder] = list()
            newOrders.extend([order for order in self.myBids.values() if order.status == OrderStatus.New])
            newOrders.extend([order for order in self.myAsks.values() if order.status == OrderStatus.New])
            self.exchangeManager.sendAllLimitOrders(newOrders)

    def buildStrategy(self, strategy: Strategy):
        bids: List[Decimal] = list()
        asks: List[Decimal] = list()

        if isinstance(strategy, BestStrategy):
            logger.debug("building bestStrategy")
            bestBid = self.exchangeManager.localOrderBook.ob.bids[0]
            bestAsk = self.exchangeManager.localOrderBook.ob.asks[0]
            myBestBids = [i for i in self.myBids.values() if i.strategy == strategy]
            myBestAsks = [i for i in self.myBids.values() if i.strategy == strategy]
            myBestBid = self.myBids.get(next(iter(myBestBids)))
            myBestAsk = self.myAsks.get(next(iter(myBestAsks)))
            if myBestBid == None:
                bids.append(bestBid + BestStrategy.offset/self.instrument.pricePrecision)
                asks.append(bestAsk - BestStrategy.offset/self.instrument.pricePrecision)
            else:
                logger.debug("need to implement")
        elif isinstance(strategy, JoinStrategy):
            bidSkewPercent, askSkewPercent = RiskManager.skewByOffset(self.instrument.base)
            logger.debug(f"{strategy} bidSkew:={bidSkewPercent:.2f}, askSkew={askSkewPercent:.2f}")
            bidSkew = floor(bidSkewPercent * SkewByOffset._maxSkew)
            askSkew = floor(askSkewPercent * SkewByOffset._maxSkew)
            bidSkew = min(bidSkew, len(self.exchangeManager.localOrderBook.ob.bids) - 1)
            askSkew = min(askSkew, len(self.exchangeManager.localOrderBook.ob.asks) - 1)
            bids.append(self.exchangeManager.localOrderBook.ob.bids[bidSkew].price)
            asks.append(self.exchangeManager.localOrderBook.ob.asks[askSkew].price)
        elif isinstance(strategy, DefensiveStrategy):
            bidSkewPercent, askSkewPercent = RiskManager.skewByOffset(self.instrument.base)
            logger.debug(f"{strategy} bidSkew:={bidSkewPercent}, askSkew={askSkewPercent}")
            bidSkew = floor(bidSkewPercent * SkewByOffset._maxSkew)
            askSkew = floor(askSkewPercent * SkewByOffset._maxSkew)
            bidIndex = min(DefensiveStrategy.level + bidSkew - 1, len(self.exchangeManager.localOrderBook.ob.bids) - 1)
            askIndex = min(DefensiveStrategy.level + askSkew - 1, len(self.exchangeManager.localOrderBook.ob.asks) - 1)
            bids.append(self.exchangeManager.localOrderBook.ob.bids[bidIndex].price)
            asks.append(self.exchangeManager.localOrderBook.ob.asks[askIndex].price)
        elif isinstance(strategy,  MultiLadderStrategy):
            bidSkewPercent, askSkewPercent = RiskManager.skewByOffset(self.instrument.base)
            logger.debug(f"{strategy} bidSkew:={bidSkewPercent}, askSkew={askSkewPercent}")
            bidSkew = floor(bidSkewPercent * SkewByOffset._maxSkew)
            askSkew = floor(askSkewPercent * SkewByOffset._maxSkew)

            bidIndex = min(MultiLadderStrategy.startLevel + bidSkew - 1, len(self.exchangeManager.localOrderBook.ob.bids) - 1)
            askIndex = min(MultiLadderStrategy.startLevel + askSkew - 1, len(self.exchangeManager.localOrderBook.ob.asks) - 1)

            for i in range(MultiLadderStrategy.nLevels):
                if i> 0:
                    bidIndex += 1
                    askIndex += 1
                    bidIndex = min(bidIndex, len(self.exchangeManager.localOrderBook.ob.bids) - 1)
                    askIndex = min(askIndex, len(self.exchangeManager.localOrderBook.ob.asks) - 1)
                bids.append(self.exchangeManager.localOrderBook.ob.bids[bidIndex].price)
                asks.append(self.exchangeManager.localOrderBook.ob.asks[askIndex].price)
        elif isinstance(strategy, MultiRandomStrategy):
            midSkew = RiskManager.midSkew(self.instrument.base)
            logger.debug(f"{strategy} midSkew:={midSkew}")
            bid = self.exchangeManager.localOrderBook.ob.bids[MultiRandomStrategy.startLevel].price
            ask = self.exchangeManager.localOrderBook.ob.asks[MultiRandomStrategy.startLevel].price
            for i in range(MultiRandomStrategy.nLevels):
                if i> 0:
                    randomOffset = random.randrange(MultiRandomStrategy.offsetMin, MultiRandomStrategy.offsetMax)
                    bid = bid - Decimal(randomOffset/(10**self.instrument.pricePrecision))
                    ask = ask + Decimal(randomOffset/(10**self.instrument.pricePrecision))
                    skew = (ask-bid)/2 * Decimal(midSkew)*SkewByOffset.skewMidFactor
                    bid -= skew
                    ask -= skew
                bids.append(bid)
                asks.append(ask)

        else:
            raise Exception(f"Strategy not implemented, {strategy}")

        return bids, asks


    def isRiskLimitTriggered(self, instrument: Instrument):
        return True if abs(RiskManager.risks[instrument.base].positionValue) > RiskManager.riskLimits[instrument.base] else False

    def riskExcess(self, instrument: Instrument):
        marketOrders: [] = []
        midPrice: Decimal = self.exchangeManager.localOrderBook.midTob
        for coin in RiskManager.risks.keys():
            if coin == Coin.USDT: continue
            if abs(RiskManager.risks[coin].positionValue) > RiskManager.riskLimits[coin]:
                usdtExcess: Decimal = abs(RiskManager.risks[coin].positionValue) - RiskManager.riskLimits[coin]
                usdtExcess += Decimal(0.1) * RiskManager.riskLimits[coin]

                orderSide = OrderSide.Sell if RiskManager.risks[coin].position > 0 else OrderSide.Buy
                excess = usdtExcess / midPrice
                marketOrders.append(SpotMarketOrder(Order.nextOrderId(),
                                                    Instruments.instruments.get(str(Instrument(coin, Coin.USDT))),
                                                    orderSide, Decimal(excess),
                                                    self.exchangeManager.localOrderBook.ob.bids[0].price))
        return marketOrders

    async def updateQuotes(self):
        self.removeFilled(self.myBids)
        self.removeFilled(self.myAsks)

        if self.isRiskLimitTriggered(self.instrument) and self.waitingForMarketOrders:
            logger.debug(f"Risk limit exceeded so no quotes generated, still waiting for market orders to be complete")
            return
        elif self.isRiskLimitTriggered(self.instrument):
            excess:List[SpotMarketOrder] = self.riskExcess(self.instrument)
            logger.debug("Risk exceeded, generating market orders")
            [self.myMarketOrders.update({order.id: order}) for order in excess]
            logger.debug("cancel any limit orders to prevent self trade")
            cancelOrders = list(self.myBids.values()) + list(self.myAsks.values())
            self.exchangeManager.cancelAllLimitOrders(cancelOrders)
            self.myBids.clear()
            self.myAsks.clear()
            #[self.exchangeManager.cancelLimitOrder(order) for order in self.myBids.values()]
            #self.myBids.clear()
            #[self.exchangeManager.cancelLimitOrder(order) for order in self.myAsks.values()]
            #self.myAsks.clear()
            [self.exchangeManager.sendMarketOrder(order) for order in excess]
            self.waitingForMarketOrders = True
        else:
            logger.debug(f"No Risk Excess - So updating Quotes")

        if self.waitingForMarketOrders: return
        for strategy in liveStrategies:
            bidPrices, askPrices = self.buildStrategy(strategy)
            if len(bidPrices) ==0 or len(askPrices) ==0:
                logger.error("build strategies failed. No bids or asks")
                return
            oldBids = [i for i in self.myBids.values() if i.strategy == strategy]
            if len(oldBids) < strategy.nLevels:
                #some bids filled/ recreate all
                self.exchangeManager.cancelAllLimitOrders(oldBids)
                for order in oldBids:
                    del self.myBids[order.id]
                for bidPrice in bidPrices:
                    bidOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), self.instrument, OrderSide.Buy
                                                          , OrderSizeInDollar.sizes[0] / bidPrice,
                                                          bidPrice, strategy)

                    logger.debug(f"adding new bid strategy {bidOrder}")
                    self.myBids[bidOrder.id] = bidOrder
            else:
                myBids = [i for i in self.myBids.values() if i.strategy== strategy]
                for i in range(len(myBids)):
                    if myBids[i].price != bidPrices[i]:
                        myBids[i].price = bidPrices[i]
                        myBids[i].status = OrderStatus.Amend
                        logger.debug(f"Amending bid {myBids[i]} original price={bidPrices[i]}")
            oldAsks = [i for i in self.myAsks.values() if i.strategy== strategy]
            if len(oldAsks) < strategy.nLevels:
                self.exchangeManager.cancelAllLimitOrders(oldAsks)
                for order in oldAsks:
                    del self.myAsks[order.id]

                for askPrice in askPrices:
                    askOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), self.instrument, OrderSide.Sell
                                                          , OrderSizeInDollar.sizes[0] / askPrice,
                                                          askPrice, strategy)

                    logger.debug(f"adding new ask strategy {askOrder}")
                    self.myAsks[askOrder.id] = askOrder
            else:
                myAsks = [i for i in self.myAsks.values() if i.strategy== strategy]
                for i in range(len(myAsks)):
                    if myAsks[i].price != askPrices[i]:
                        myAsks[i].price = askPrices[i]
                        myAsks[i].status = OrderStatus.Amend
                        logger.debug(f"Amending ask  {myAsks[i]} original price={askPrices[i]}")

        newOrders = ([order for order in self.myBids.values() if order.status == OrderStatus.New]
                     + [order for order in self.myAsks.values() if order.status == OrderStatus.New])
        if len(newOrders) > 0 :
            self.exchangeManager.sendAllLimitOrders(newOrders)

        self.amendOrders(self.myBids)
        self.amendOrders(self.myAsks)

    def amendOrders(self, orders):
        for key in list(orders.keys()):
            order: SpotLimitOrder = orders[key]
            if order.status == OrderStatus.Amend:
                if self.exchangeManager.amendLimitOrder(order):
                    logger.debug(f"successfully amended order {order}")
                else:
                    logger.error(f"Amend order failed {order}")
                    del orders[key]

    def removeFilled(self, orders):
        for key in list(orders.keys()):
            if orders[key].filledAmount > 0 and TOUCHED == Touched.Refresh:
                self.removeOrder(orders, orders[key])
            elif (orders[key].filledAmount / orders[key].amount) > 0.9:
                self.removeOrder(orders, orders[key])

    def removeOrder(self, orders, order):
        self.exchangeManager.cancelLimitOrder(order)
        order.status = OrderStatus.Cancelled
        logger.debug(f"order cancelled {order})")
        del orders[order.id]


    async def run(self):
        while Static.KeepRunning:
            try:
                result = await self.exchangeManager.quotesQueue.get()
                logger.debug(f"result received : {result}")
                if isinstance(result, FilledOrder):
                    if result.id in self.myMarketOrders:
                        logger.debug("result is a market order")
                        self.waitingForMarketOrders = False
                        self.myMarketOrders[result.id].filledAmount += result.filledAmount
                        self.myMarketOrders[result.id].completionTime = int(time.time())
                        self.executedOrders.append(copy.copy(self.myMarketOrders[result.id]))
                    else:
                        logger.debug(f"result is a limit order : {result}")
                        order = self.myBids[result.id] if result.side == OrderSide.Buy else self.myAsks[result.id]
                        order.filledAmount += result.filledAmount
                        order.status = OrderStatus.Filled
                        order.completionTime = int(time.time())
                        self.executedOrders.append(copy.copy(order))
            except:
                logger.exception('')
            finally:
                logger.debug(f"updating quotes")  # always do this
                await self.updateQuotes()

        logging.error("Kill Switch Triggered")

if __name__ == '__main__':
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))

    sInstrument = "BTC_USDT"
    instrument = Instruments.instruments.get(sInstrument)

    exchangeManager = GateIOManager(instrument, conn)
    quoteManager = QuoteManager(Strategy.Best, instrument, exchangeManager)

    instrument = Instruments.instruments.get("BTC_USDT")

    quoteManager.initialize()
    exchangeManager.initialize()

    loop = asyncio.get_event_loop()
    loop.create_task(quoteManager.run())
    loop.create_task(exchangeManager.run())
    loop.create_task(exchangeManager.runMyOrderUpdate())
    loop.create_task(conn.run())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()