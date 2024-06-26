import asyncio
import logging
from typing import List, Dict

import Static
from Test.SumulatedMarketMaker.MatchingEngine import MatchingEngine
from Test.SumulatedMarketMaker.SimulatedLocalOrderBook import SimulatedLocalOrderBook
from connectivity.LocalOrderBookBase import  OrderBookEntry
from connectivity.gateio.ws import Connection
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from core.Instrument import Instrument
from core.MyEnums import OrderStatus
from core.Orders import SpotLimitOrder, SpotMarketOrder

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
Static.appLoggers.append(logger)


class SimulatedExchange(ExchangeManagerBase):
    def __init__(self, instruments: List[Instrument], conn: Connection):
        super().__init__(instruments, conn)
        self.localOrderBooks: Dict[Instrument, SimulatedLocalOrderBook] = dict()
        [self.localOrderBooks.update({instrument:SimulatedLocalOrderBook(instrument, self.localOrderBookUpdateQueue[instrument])}) for instrument in instruments]
        self.matchingEngine = MatchingEngine(self.myOrdersUpdateQueue)
        loop = asyncio.get_event_loop()
        loop.create_task(self.matchingEngine.runLmitOrderMatcher())
        loop.create_task(self.matchingEngine.runMarketOrderMatcher())


    def initialize(self):
        [localOrderBook.initialize() for localOrderBook in self.localOrderBooks.values()]

    def sendLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"send limitOrder enter  : {order}")
        order.status = OrderStatus.Active
        entry: OrderBookEntry = OrderBookEntry(order.price, order.amount)
        self.localOrderBooks[order.instrument].myOb[order.id] = order
        self.matchingEngine.sendLimitOrder(order)
        self.localOrderBooks[order.instrument].buildOrderBook()

    def sendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        logger.debug(f"sendAllLimitOrders enter ")
        for order in orders:
            order.status = OrderStatus.Active
            self.sendLimitOrder(order)


    def sendMarketOrder(self, order: SpotMarketOrder):
        logger.debug(f"send MarketOrder enter  : {order}")
        order.status = OrderStatus.Active
        self.matchingEngine.sendMarketOrder(order)
        return True

    def amendLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"amend limitOrder enter  : {order}")
        order.status = OrderStatus.Active
        self.localOrderBooks[order.instrument].myOb[order.id] = order
        self.matchingEngine.amendLimitOrder(order)
        self.localOrderBooks[order.instrument].buildOrderBook()
        return True


    def cancelLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"cancel limitOrder enter  : {order}")
        order.status = OrderStatus.Cancelled
        del self.localOrderBooks[order.instrument].myOb[order.id]
        self.matchingEngine.cancelLimitOrder(order)
        self.localOrderBooks[order.instrument].buildOrderBook()

    def cancelAllLimitOrders(self, orders: List[SpotLimitOrder]):
        if len(orders) > 0:
            logger.debug(f"cancelAllLimitOrders enter ")
            for order in orders:
                self.cancelLimitOrder(order)


    def amendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        if len(orders) > 0:
            logger.debug(f"amendAllLimitOrders enter ")
            for order in orders:
                self.amendLimitOrder(order)


    def cancelOrderWithParms(self):
        pass

    def orderStatus(self):
        pass
