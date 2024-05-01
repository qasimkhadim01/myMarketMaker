import asyncio
from abc import ABC
from decimal import Decimal
from typing import List

import Static
from connectivity.LocalOrderBookBase import LocalOrderBookBase
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, WebSocketResponse
from core.Instrument import Instrument
from core.Orders import SpotLimitOrder, SpotMarketOrder, FilledOrder
import logging

from marketmaker.RiskManager import RiskManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



class ExchangeManagerBase(ABC):
    def __init__(self, instrument: Instrument, conn: Connection):
        self.instrument = instrument
        self.conn = conn
        self.quotesQueue = asyncio.Queue()
        self.orderBookUpdateQueue: asyncio.Queue = asyncio.Queue()
        self.myOrdersUpdateQueue = asyncio.Queue()
        self.topOfBookQueue = asyncio.Queue()
        self.requestCounterId = 0
        self.localOrderBook = None

    def initialize(self):
        self.localOrderBook.initialize()  # only start receiving call backs once all other essentials init

    def release(self):
        self.conn.close()

    def LocalOrderBook(self) -> LocalOrderBookBase:
        return self.localOrderBook

    @property
    def nextRequestId(self):
        requestId = "t-req_" + str(self.instrument) + "_" + Api.subAccount + "_" + str(self.requestCounterId)
        self.requestCounterId += 1
        return requestId

    async def run(self):
        while Static.KeepRunning:
            result = await self.orderBookUpdateQueue.get()
            logger.debug(f"order book update")
            await self.quotesQueue.put(result)
        logging.error("Kill Switch Triggered")

    async def runMyOrderUpdate(self):
        while Static.KeepRunning:
            try:
                filledOrders = await self.myOrdersUpdateQueue.get()
                logger.debug(f"received myOrderUpdate")
                if isinstance(filledOrders, list):
                    filledOrderAggregates: dict[str, FilledOrder] = dict()
                    for filledOrder in filledOrders:
                        # simply sum of the volume here, as the VWAP is only important for risk position
                        RiskManager.onPositionUpdate(filledOrder)
                        if filledOrder.id not in filledOrderAggregates.keys():
                            filledOrderAggregates[filledOrder.id] = FilledOrder(filledOrder.id, filledOrder.instrument
                                            , filledOrder.side, Decimal(0.0)
                                            , filledOrder.price, filledOrder.role)
                        filledOrderAggregates[filledOrder.id].filledAmount += filledOrder.filledAmount
                        filledOrderAggregates[filledOrder.id].amount += filledOrder.amount
                    [await self.quotesQueue.put(filledOrder) for filledOrder in filledOrderAggregates.values()]
            except:
                logger.exception('')
        logging.error("Kill Switch Triggered")

    def sendLimitOrder(self, order: SpotLimitOrder):
        pass

    def sendMarketOrder(self, order: SpotMarketOrder):
        pass

    def cancelLimitOrder(self, order):
        pass

    def cancelAllLimitOrders(self, orders: List[SpotLimitOrder]):
        pass

    def amendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        pass

    def sendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        pass

    def amendLimitOrder(self, order: SpotLimitOrder):
        pass
