import asyncio
import logging
from random import random
from typing import List

import Static
from core.MyEnums import OrderSide, Role
from core.Orders import SpotLimitOrder, FilledOrder, Order, SpotMarketOrder

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
Static.appLoggers.append(logger)


class MatchingEngine:
    def __init__(self, myOrdersUpdateQueue: asyncio.Queue):
        self.bids: dict[str, SpotLimitOrder] = dict()
        self.asks: dict[str, SpotLimitOrder] = dict()
        self.marketOrders: dict[str, SpotMarketOrder] = dict()
        self.myOrdersUpdateQueue = myOrdersUpdateQueue
        self.partialSplit = 2
    def sendLimitOrder(self, order: SpotLimitOrder):
        if order.side == OrderSide.Buy:
            self.bids[order.id] = order

        if order.side == OrderSide.Sell:
            self.asks[order.id] = order

    def sendMarketOrder(self, order: SpotMarketOrder):
        self.marketOrders[order.id] = order
        logger.debug(f"Received new Market Order")

    def amendLimitOrder(self, order: SpotLimitOrder):
        if order.side == OrderSide.Buy:
            if order.id in self.bids:
                self.bids[order.id] = order
        if order.side == OrderSide.Sell:
            if order.id in self.asks:
                self.asks[order.id] = order

    def cancelLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"cancelling {order}")
        if order.side == OrderSide.Buy:
            if order.id in self.bids:
                logger.debug(f"found order to cancel {order}")
                del self.bids[order.id]
        if order.side == OrderSide.Sell:
            if order.id in self.asks:
                logger.debug(f"found order to cancel {order}")
                del self.asks[order.id]

    def partialSlice(self, matchedOrder: Order):
        filledOrders: List[FilledOrder] = list()
        for i in range(0, self.partialSplit):
            filledOrder: FilledOrder = FilledOrder(matchedOrder.id, matchedOrder.instrument,
                                                       matchedOrder.side, matchedOrder.amount/self.partialSplit, matchedOrder.price,
                                                       Role.Maker)
            filledOrders.append(filledOrder)
        return filledOrders

    async def runLmitOrderMatcher(self):
        while Static.KeepRunning:
            await asyncio.sleep(60)
            rnd = round(random())
            partialFilledOrders: List[FilledOrder] = list()
            if rnd == 0 and len(self.bids) > 0:
                matchedOrder = self.bids.get(next(iter(self.bids)))
                partialFilledOrders = self.partialSlice(matchedOrder)
                del self.bids[matchedOrder.id]
            elif rnd == 1 and len(self.asks) > 0:
                matchedOrder = self.asks.get(next(iter(self.asks)))
                partialFilledOrders = self.partialSlice(matchedOrder)
                del self.asks[matchedOrder.id]
            filledOrders: List[Order] = list()
            for partialMatchOrder in partialFilledOrders:

                filledOrder: FilledOrder = FilledOrder(partialMatchOrder.id, partialMatchOrder.instrument,
                                                       partialMatchOrder.side, partialMatchOrder.amount, partialMatchOrder.price,
                                                       partialMatchOrder.role)


                filledOrders.append(filledOrder)
                logger.debug(f"matched market  {filledOrder}")
            if len(filledOrders) > 0: await self.myOrdersUpdateQueue.put(filledOrders)

    async def runMarketOrderMatcher(self):
        while Static.KeepRunning:
            await asyncio.sleep(3)

            partialFilledOrders: List[FilledOrder] = list()
            if len(self.marketOrders) > 0:
                matchedOrder = self.marketOrders.get(next(iter(self.marketOrders)))
                partialFilledOrders = self.partialSlice(matchedOrder)
                del self.marketOrders[matchedOrder.id]
            filledOrders: List[Order] = list()
            for partialMatchOrder in partialFilledOrders:

                filledOrder: FilledOrder = FilledOrder(partialMatchOrder.id, partialMatchOrder.instrument,
                                                       partialMatchOrder.side, partialMatchOrder.amount, partialMatchOrder.price,
                                                       partialMatchOrder.role)


                filledOrders.append(filledOrder)
                logger.debug(f"matched market  {filledOrder}")
            if len(filledOrders) > 0: await self.myOrdersUpdateQueue.put(filledOrders)


