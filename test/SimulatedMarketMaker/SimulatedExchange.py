import asyncio
import logging
from typing import List

from Test.SumulatedMarketMaker.MatchingEngine import MatchingEngine
from Test.SumulatedMarketMaker.SimulatedLocalOrderBook import SimulatedLocalOrderBook
from connectivity.LocalOrderBookBase import LocalOrderBookBase
from connectivity.gateio.ws import Connection
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from core.Instrument import Instrument
from core.MyEnums import OrderStatus, Role
from core.Orders import SpotLimitOrder, SpotMarketOrder, FilledOrder

logger = logging.getLogger(__name__)


class SimulatedExchange(ExchangeManagerBase):
    def __init__(self, instrument: Instrument, conn: Connection):
        super().__init__(instrument, conn)
        self.localOrderBook: LocalOrderBookBase = SimulatedLocalOrderBook(self.instrument,  self.orderBookUpdateQueue)
        self.matchingEngine = MatchingEngine(self.myOrdersUpdateQueue)
        loop = asyncio.get_event_loop()
        loop.create_task(self.matchingEngine.runLmitOrderMatcher())
        loop.create_task(self.matchingEngine.runMarketOrderMatcher())

    def sendLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"send limitOrder enter  : {order}")
        order.status = OrderStatus.Active
        self.matchingEngine.sendLimitOrder(order)

    def sendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        logger.debug(f"cancelAllLimitOrders enter ")
        for order in orders:
            order.status = OrderStatus.Active
            self.sendLimitOrder(order)


    def sendMarketOrder(self, order: SpotMarketOrder):
        logger.debug(f"send MarketOrder enter  : {order}")
        order.status = OrderStatus.Active
        self.matchingEngine.sendMarketOrder(order)

    def amendLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"amend limitOrder enter  : {order}")
        order.status = OrderStatus.Active
        self.matchingEngine.amendLimitOrder(order)
        return True


    def cancelLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"cancel limitOrder enter  : {order}")
        order.status = OrderStatus.Cancelled
        self.matchingEngine.cancelLimitOrder(order)

    def cancelAllLimitOrders(self, orders: List[SpotLimitOrder]):
        logger.debug(f"cancelAllLimitOrders enter ")
        for order in orders:
            self.cancelLimitOrder(order)

    def amendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        logger.debug(f"amendAllLimitOrders enter ")
        for order in orders:
            self.amendLimitOrder(order)



    def cancelOrderWithParms(self):
        pass

    def orderStatus(self):
        pass
