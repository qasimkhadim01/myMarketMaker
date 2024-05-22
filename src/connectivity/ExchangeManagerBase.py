import asyncio
from abc import ABC
from decimal import Decimal
from typing import List, Dict

import Static
from connectivity.LocalOrderBookBase import LocalOrderBookBase
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, WebSocketResponse
from core.Instrument import Instrument
from core.Orders import SpotLimitOrder, SpotMarketOrder, FilledOrder
import logging

from marketmaker.RiskManager import RiskManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
Static.appLoggers.append(logger)


class ExchangeManagerBase(ABC):
    def __init__(self, instruments: List[Instrument], conn: Connection):
        self.instruments = instruments
        self.conn = conn
        self.quotesQueue:Dict[Instrument, asyncio.Queue] = dict()
        [self.quotesQueue.update({instrument:asyncio.Queue()}) for instrument in instruments]
        self.localOrderBookUpdateQueue:Dict[Instrument, asyncio.Queue] = dict()
        [self.localOrderBookUpdateQueue.update({instrument:asyncio.Queue()}) for instrument in instruments]
        self.myOrdersUpdateQueue = asyncio.Queue()

        self.topOfBookQueue:Dict[Instrument, asyncio.Queue] = dict()
        [self.topOfBookQueue.update({instrument: asyncio.Queue()}) for instrument in instruments]
        self.requestCounterId = 0
        self.localOrderBooks:Dict[Instrument, LocalOrderBookBase] = dict()
    def release(self):
        self.conn.close()

    async def run(self):
        async def process(instrument:Instrument, queue:asyncio.Queue):
            while Static.KeepRunning:
                result = await queue.get()
                await self.quotesQueue[instrument].put(result)
            logging.error("Kill Switch Triggered")

        loop = asyncio.get_event_loop()


        [loop.create_task(process(item[0], item[1])) for item in self.localOrderBookUpdateQueue.items()]


    async def runMyOrderUpdate(self):
        while Static.KeepRunning:
            try:
                filledOrders = await self.myOrdersUpdateQueue.get()
                logger.debug(f"received myOrderUpdate")
                if isinstance(filledOrders, list):
                    filledOrderAggregates: dict[str, FilledOrder] = dict()
                    for filledOrder in filledOrders:
                        # simply sum of the volume here, as the VWAP is only important for risk position
                        # position is updated een
                        RiskManager.onPositionUpdate(filledOrder)
                        if filledOrder.id not in filledOrderAggregates.keys():
                            filledOrderAggregates[filledOrder.id] = FilledOrder(filledOrder.id, filledOrder.instrument
                                            , filledOrder.side, Decimal(0.0)
                                            , filledOrder.price, filledOrder.role)
                        filledOrderAggregates[filledOrder.id].filledAmount += filledOrder.filledAmount
                        filledOrderAggregates[filledOrder.id].amount += filledOrder.amount
                    [await self.quotesQueue[filledOrder.instrument].put(filledOrder) for filledOrder in filledOrderAggregates.values()]
                else:
                    logger.error(f"not expecting {filledOrders}")
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
