import asyncio
import copy
import random

from sortedcontainers import SortedList

from connectivity import LocalOrderBookBase
from connectivity.LocalOrderBookBase import OrderBookEntry
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
from marketmaker.Strategy import Strategy, liveStrategies, DefensiveStrategy, TOUCHED, Touched, \
    MultiRandomStrategy, LadderStrategy, JoinStrategy, BestStrategy
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Static.appLoggers.append(logger)

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
        # cancel all quotes
        [self.exchangeManager.cancelLimitOrder(order) for order in self.myBids.values()]
        self.myBids.clear()
        [self.exchangeManager.cancelLimitOrder(order) for order in self.myAsks.values()]
        self.myAsks.clear()


    def initialize(self):
        if len(self.exchangeManager.localOrderBooks[self.instrument].ob.bids) > 0:
            for strategy in liveStrategies:
                bidPrices, askPrices = self.buildStrategy(strategy, self.exchangeManager.localOrderBooks[self.instrument].ob.bids, self.exchangeManager.localOrderBooks[self.instrument].ob.asks)
                for bidPrice in bidPrices:
                    bidOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), self.instrument, OrderSide.Buy
                                                          , strategy.buySizeInUsd / bidPrice,
                                                          bidPrice, strategy)
                    self.myBids.update({bidOrder.id: bidOrder})
                for askPrice in askPrices:
                    askOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), self.instrument, OrderSide.Sell
                                                          , strategy.sellSizeInUsd / askPrice,
                                                          askPrice, strategy)


                    self.myAsks.update({askOrder.id: askOrder})

            newOrders:List[SpotLimitOrder] = list()
            newOrders.extend([order for order in self.myBids.values() if order.status == OrderStatus.New])
            newOrders.extend([order for order in self.myAsks.values() if order.status == OrderStatus.New])
            [logger.debug(f"New {order}") for order in newOrders]
            self.exchangeManager.sendAllLimitOrders(newOrders)

    def strippedBest(self):
        topOfBookBid = copy.deepcopy(self.exchangeManager.localOrderBooks[self.instrument].topOfBookBid)
        topOfBookAsk = copy.deepcopy(self.exchangeManager.localOrderBooks[self.instrument].topOfBookAsk)

        myBestBid = [i for i in self.myBids.values() if isinstance(i.strategy, BestStrategy)]
        myBestAsk = [i for i in self.myAsks.values() if isinstance(i.strategy, BestStrategy)]
        if len(myBestBid) > 0 and myBestBid[0].price == topOfBookBid.price:
            topOfBookBid.amount -= myBestBid[0].amount
        if len(myBestAsk) > 0 and myBestAsk[0].price == topOfBookAsk.price:
            topOfBookAsk.amount -= myBestAsk[0].amount

        return topOfBookBid, topOfBookAsk
    def strippedOrderBook(self, localOrderBook: LocalOrderBookBase):
        marketBids = copy.deepcopy(localOrderBook.ob.bids[:20])
        marketAsks = copy.deepcopy(localOrderBook.ob.asks[:20])
        bidsAsList = list(self.myBids.values())
        asksAsList = list(self.myAsks.values())


        matches = [i for i, item in enumerate(marketBids) if
                   item.price in [x.price for x in bidsAsList]]

        for i in range(len(matches)):
            marketBids[matches[i]].amount -= bidsAsList[i].amount
        marketBids = [x for x in marketBids if Decimal(x.amount) > 0.0]

        matches = [i for i, item in enumerate(marketAsks) if
                   item.price in [x.price for x in asksAsList]]

        for i in range(len(matches)):
            marketAsks[matches[i]].amount -= asksAsList[i].amount

        marketAsks = [x for x in marketAsks if x.amount > 0.0]
        return SortedList(marketBids, key=lambda x: -x.price), SortedList(marketAsks)

    def buildStrategy(self, strategy: Strategy, obBids:SortedList[OrderBookEntry], obAsks:SortedList[OrderBookEntry]):
        bids: List[Decimal] = list()
        asks: List[Decimal] = list()

        if isinstance(strategy, BestStrategy):
            strippedBestBid, strippedBestAsk = self.strippedBest()
            if strippedBestBid.amount <=0:
                strategyBid = strippedBestBid.price
            else:
                strategyBid = round(strippedBestBid.price + Decimal(BestStrategy.spreadOffset / (10 ** self.instrument.pricePrecision))
                          , self.instrument.pricePrecision)
            if strippedBestAsk.amount <=0:
                strategyAsk = strippedBestAsk.price
            else:
                strategyAsk = round(strippedBestAsk.price - Decimal(BestStrategy.spreadOffset/(10**self.instrument.pricePrecision))
                                  ,self.instrument.pricePrecision)
            marketSpread = (strategyAsk -strategyBid)*10**self.instrument.pricePrecision
            if marketSpread >= BestStrategy.minSpread:
                bids.append(strategyBid)
                asks.append(strategyAsk)
            else:
            #    bids.append(strippedBestBid.price)
            #    asks.append(strippedBestAsk.price)
                logger.debug(f"MarketSpread = {marketSpread} is tighter than Best Strategy Spread={BestStrategy.minSpread}")

        elif isinstance(strategy, JoinStrategy):
            bidSkewPercent, askSkewPercent = RiskManager.skewByOffset(self.instrument.base)
            logger.debug(f"{strategy.__class__.__name__} bidSkew:={bidSkewPercent:.2f}, askSkew={askSkewPercent:.2f}")
            bidSkew = floor(bidSkewPercent * SkewByOffset._maxSkew)
            askSkew = floor(askSkewPercent * SkewByOffset._maxSkew)
            bidSkew = min(bidSkew, len(obBids) - 1)
            askSkew = min(askSkew, len(obAsks) - 1)
            bids.append(obBids[bidSkew].price)
            asks.append(obAsks[askSkew].price)
        elif isinstance(strategy, DefensiveStrategy):
            #logger.debug("building defensiveStrategy")
            bidSkewPercent, askSkewPercent = RiskManager.skewByOffset(self.instrument.base)
            logger.debug(f"{strategy} bidSkew:={bidSkewPercent}, askSkew={askSkewPercent}")
            bidSkew = floor(bidSkewPercent * SkewByOffset._maxSkew)
            askSkew = floor(askSkewPercent * SkewByOffset._maxSkew)
            bidIndex = min(DefensiveStrategy.level + bidSkew - 1, len(obBids) - 1)
            askIndex = min(DefensiveStrategy.level + askSkew - 1, len(obAsks) - 1)
            bids.append(obBids[bidIndex].price)
            asks.append(obAsks[askIndex].price)
        elif isinstance(strategy, LadderStrategy):
            #logger.debug("building ladderStrategy")
            bidSkewPercent, askSkewPercent = RiskManager.skewByOffset(self.instrument.base)
            logger.debug(f"{strategy.__class__.__name__} bidSkew:={bidSkewPercent}, askSkew={askSkewPercent}")
            bidSkew = floor(bidSkewPercent * SkewByOffset._maxSkew)
            askSkew = floor(askSkewPercent * SkewByOffset._maxSkew)

            bidIndex = min(LadderStrategy.startLevel + bidSkew - 1, len(obBids) - 1)
            askIndex = min(LadderStrategy.startLevel + askSkew - 1, len(obAsks) - 1)

            for i in range(LadderStrategy.nLevels):
                if i> 0:
                    bidIndex += 1
                    askIndex += 1
                    bidIndex = min(bidIndex, len(obBids) - 1)
                    askIndex = min(askIndex, len(obAsks) - 1)
                bids.append(obBids[bidIndex].price)
                asks.append(obAsks[askIndex].price)
        elif isinstance(strategy, MultiRandomStrategy):
            logger.debug("building MultiRandomStrategy")
            midSkew = RiskManager.midSkew(self.instrument.base)
            logger.debug(f"{strategy} midSkew:={midSkew}")
            bid = obBids[MultiRandomStrategy.startLevel].price
            ask = obAsks[MultiRandomStrategy.startLevel].price
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


        #[logger.debug(f"bid={round(bid, self.instrument.pricePrecision)}") for bid in bids]
        #[logger.debug(f"ask={round(ask, self.instrument.pricePrecision)}") for ask in asks]
        return bids, asks




    def isRiskLimitTriggered(self, instrument: Instrument):
        return True if abs(RiskManager.risks[instrument.base].positionValue) > RiskManager.riskLimits[instrument.base] else False

    def riskExcess(self, instrument: Instrument):
        marketOrders: [] = []
        midPrice: Decimal = self.exchangeManager.localOrderBooks[self.instrument].midTob
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
                                                    self.exchangeManager.localOrderBooks[self.instrument].ob.bids[0].price))
        return marketOrders

    async def updateQuotes(self):
        self.removeFilled(self.myBids)
        self.removeFilled(self.myAsks)

        if self.isRiskLimitTriggered(self.instrument) and self.waitingForMarketOrders:
            logger.debug(f"Risk limit exceeded, so no market orders  generated waitingForMarketOrdrs={self.waitingForMarketOrders}")
        elif self.isRiskLimitTriggered(self.instrument):
            excess:List[SpotMarketOrder] = self.riskExcess(self.instrument)
            logger.debug("Risk exceeded, generating market orders")
            [self.myMarketOrders.update({order.id: order}) for order in excess]
            logger.debug("cancel any limit orders to prevent self trade")
            if excess[0].side == OrderSide.Buy:
                self.exchangeManager.cancelAllLimitOrders(list(self.myAsks.values()))
                logger.debug("cancelled all orders sell side")
                self.myAsks.clear()
            else:
                self.exchangeManager.cancelAllLimitOrders(list(self.myBids.values()))
                logger.debug("cancelled all buy orders")
                self.myBids.clear()
            logger.error("sleep for 2 seconds, let cancel orders complete")
            await asyncio.sleep(2)
            #[self.exchangeManager.cancelLimitOrder(order) for order in self.myBids.values()]
            #self.myBids.clear()
            #[self.exchangeManager.cancelLimitOrder(order) for order in self.myAsks.values()]
            #self.myAsks.clear()
            if  self.exchangeManager.sendMarketOrder(excess[0]):
                self.waitingForMarketOrders = True
            else:
                self.waitingForMarketOrders = False
                logger.error("New Market Order returned false, try again")
                await asyncio.sleep(2)
                
        elif not self.isRiskLimitTriggered(self.instrument):
            self.waitingForMarketOrders = False

        #if self.waitingForMarketOrders: return
        #logger.debug("updating quotes enter")
        strippedObBids, strippedObAsks = self.strippedOrderBook(self.exchangeManager.localOrderBooks[self.instrument])

        for strategy in liveStrategies:
            bidPrices, askPrices = self.buildStrategy(strategy, strippedObBids, strippedObAsks)
            #bidPrices, askPrices = self.buildStrategy(strategy, self.exchangeManager.localOrderBook.bids, self.exchangeManager.localOrderBook.asks)
            if len(bidPrices) ==0 or len(askPrices) ==0:
                logger.error("build strategies returned no bids or asks")
                continue
            oldBids = [i for i in self.myBids.values() if i.strategy == strategy]
            if len(oldBids) < strategy.nLevels:
                logger.debug(f"{strategy.__class__.__name__} Number of current bids={len(oldBids)} strategy expects={strategy.nLevels}")
                logger.debug("recreating strategy quotes")
                self.exchangeManager.cancelAllLimitOrders(oldBids)
                for order in oldBids:
                    del self.myBids[order.id]
                for bidPrice in bidPrices:
                    bidOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), self.instrument, OrderSide.Buy
                                                          , strategy.buySizeInUsd / bidPrice,
                                                          bidPrice, strategy)

                    #logger.debug(f"adding new bid strategy {bidOrder}")
                    self.myBids[bidOrder.id] = bidOrder
            else:
                myBids = [i for i in self.myBids.values() if i.strategy== strategy]
                for i in range(len(myBids)):
                    if myBids[i].price != bidPrices[i]:
                        #myBids[i].amount *= bidPrices[i]/myBids[i].price only price or amount can be changed not both
                        myBids[i].price = bidPrices[i]
                        myBids[i].status = OrderStatus.Amend
                        #logger.info(f"Amended bid {myBids[i]}")
            oldAsks = [i for i in self.myAsks.values() if i.strategy== strategy]
            if len(oldAsks) < strategy.nLevels:
                logger.debug(f"{strategy.__class__.__name__} Number of current asks={len(oldAsks)} strategy expects={strategy.nLevels}")
                logger.debug("recreating strategy quotes")
                self.exchangeManager.cancelAllLimitOrders(oldAsks)
                for order in oldAsks:
                    del self.myAsks[order.id]

                for askPrice in askPrices:
                    askOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), self.instrument, OrderSide.Sell
                                                          , strategy.sellSizeInUsd / askPrice,
                                                          askPrice, strategy)

                    #logger.debug(f"adding new ask strategy {askOrder}")
                    self.myAsks[askOrder.id] = askOrder
            else:
                myAsks = [i for i in self.myAsks.values() if i.strategy== strategy]
                for i in range(len(myAsks)):
                    if myAsks[i].price != askPrices[i]:
                        #myAsks[i].amount *= askPrices[i] / myAsks[i].price only price or amount can be changed not both
                        myAsks[i].price = askPrices[i]
                        myAsks[i].status = OrderStatus.Amend
                       # logger.info(f"Amended ask  Current={myAsks[i]}")


        newOrders = ([order for order in self.myBids.values() if order.status == OrderStatus.New]
                     + [order for order in self.myAsks.values() if order.status == OrderStatus.New])
        if len(newOrders) > 0 :
            [logger.debug(f"New {order}") for order in newOrders]
            self.exchangeManager.sendAllLimitOrders(newOrders)

        self.amendOrders(self.myBids)
        self.amendOrders(self.myAsks)

    def amendOrders(self, orders):
        [logger.debug(f"Amend {order}") for order in orders.values() if order.status == OrderStatus.Amend]
        failedOrders:List[SpotLimitOrder] = self.exchangeManager.amendAllLimitOrders(list(order for order in orders.values() if order.status == OrderStatus.Amend))
        if failedOrders is not None:
            for failedOrder in failedOrders:
                logger.error(f"Error: Amend order failed {failedOrder}")
                logger.error("Error: Try a single amend instead")
                if not self.exchangeManager.amendLimitOrder(orders[failedOrder.id]):
                    logger.error("Error: Single amend failed")
                    logger.error("Cancel order now")
                    self.exchangeManager.cancelLimitOrder(orders[failedOrder.id])
                    if failedOrder.id in orders:
                        del orders[failedOrder.id]
                        logger.error("Remove order from orders collection")
                    else:
                        logger.error(f"Error: Delete order failed, as probably  filled {failedOrder}")




    def amendOrdersold(self, orders):
        for key in list(orders.keys()):
            order: SpotLimitOrder = orders[key]
            if order.status == OrderStatus.Amend:
                if not self.exchangeManager.amendLimitOrder(order):
                    logger.error(f"Amend order failed {order}")
                    del orders[key]

    def removeFilled(self, orders):
        for key in list(orders.keys()):
            if orders[key].filledAmount > 0 and TOUCHED == Touched.Refresh:
                self.removeFilledOrder(orders, orders[key])
            elif (orders[key].filledAmount / orders[key].amount) > 0.9:
                self.removeFilledOrder(orders, orders[key])

    def removeFilledOrder(self, orders, order):
        self.exchangeManager.cancelLimitOrder(order)
        order.status = OrderStatus.Cancelled
        logger.debug(f"order cancelled {order})")
        del orders[order.id]


    async def run(self):
        while Static.KeepRunning:
            try:
                result = await self.exchangeManager.quotesQueue[self.instrument].get()
                logger.debug(f"result received : {result}")
                if isinstance(result, FilledOrder):
                    if result.id in self.myMarketOrders:
                        logger.info("result is a market order")
                        self.waitingForMarketOrders = False
                        self.myMarketOrders[result.id].filledAmount += result.filledAmount
                        self.myMarketOrders[result.id].completionTime = int(time.time())
                        self.executedOrders.append(copy.copy(self.myMarketOrders[result.id]))
                    elif result.id in self.myBids or result.id in self.myAsks:
                        logger.info(f"result is a limit order : {result}")
                        order = self.myBids[result.id] if result.side == OrderSide.Buy else self.myAsks[result.id]
                        order.filledAmount += result.filledAmount
                        order.status = OrderStatus.Filled
                        order.completionTime = int(time.time())
                        self.executedOrders.append(copy.copy(order))
                    else:
                        logger.error(f"result is a {result}")
            except:
                logger.exception('')
            finally:
                await self.updateQuotes()

        logging.error("Kill Switch Triggered")

if __name__ == '__main__':
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))

    sInstrument = "BTC_USDT"
    instrument = Instruments.instruments.get(sInstrument)

    exchangeManager = GateIOManager(instrument, conn)
    quoteManager = QuoteManager(instrument, exchangeManager)

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