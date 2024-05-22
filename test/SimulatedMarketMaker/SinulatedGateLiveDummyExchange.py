import asyncio
import logging
from typing import List

import Static
from Test.SumulatedMarketMaker.MatchingEngine import MatchingEngine
from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio.ws import Connection
from core.Instrument import Instrument
from core.MyEnums import OrderStatus
from core.Orders import SpotLimitOrder, SpotMarketOrder

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
Static.appLoggers.append(logger)


class SimulatedGateLiveDummyExchange(GateIOManager):
    def __init__(self, instruments: List[Instrument], conn: Connection):
        super().__init__(instruments, conn)
        self.matchingEngine = MatchingEngine(self.myOrdersUpdateQueue)
        loop = asyncio.get_event_loop()
        loop.create_task(self.matchingEngine.runLmitOrderMatcher())
        loop.create_task(self.matchingEngine.runMarketOrderMatcher())

    def sendLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"send limitOrder enter  : {order}")
        order.status = OrderStatus.Active
        self.matchingEngine.sendLimitOrder(order)

    def sendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        logger.debug(f"sendAllLimitOrders enter ")
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
