import logging

from connectivity.LocalOrderBook import LocalOrderBook
from connectivity.gateio.ws import Connection
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from core.MyEnums import OrderStatus
from core.Orders import SpotLimitOrder, SpotMarketOrder, FilledOrder

logger = logging.getLogger(__name__)


class SimulatedExchange(ExchangeManagerBase):
    def __init__(self, instrument: str, conn: Connection):
        super().__init__(instrument, conn)
        self.localOrderBook = LocalOrderBook(self.instrument,  self.orderBookUpdateQueue)

    def sendLimitOrder(self, order: SpotLimitOrder):
        order.status = OrderStatus.Active

    def sendMarketOrder(self, order: SpotMarketOrder):
        order.status = OrderStatus.Active
        filledOrder: FilledOrder = FilledOrder(order.id, order.instrument
                                               , order.side, order.amount, order.price)

    def amendLimitOrder(self, order: SpotLimitOrder):
        order.status = OrderStatus.Amend


    def cancelOrder(self):
        pass

    def cancelOrderWithParms(self):
        pass

    def orderStatus(self):
        pass
