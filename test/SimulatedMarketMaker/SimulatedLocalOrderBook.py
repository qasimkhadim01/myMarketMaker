import asyncio
import itertools
import logging
import typing
from datetime import datetime
from decimal import Decimal
from random import random

import Static
from connectivity.LocalOrderBookBase import LocalOrderBookBase, OrderBookEntry, OrderBook
from core.Instrument import Instrument

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SimulatedLocalOrderBook(LocalOrderBookBase):
    def __init__(self, instrument: Instrument, orderBookUpdateQueue: asyncio.Queue):
        super().__init__(instrument, orderBookUpdateQueue)
        self.q = asyncio.Queue()
        loop = asyncio.get_event_loop()
        self.ob = loop.run_until_complete(self.construct_base_order_book())
        self.timestamp = datetime.now()
    @property
    def id(self):
        return self.ob.id

    @property
    def asks(self):
        return self.ob.asks

    @property
    def bids(self):
        return self.ob.bids

    async def construct_base_order_book(self) -> OrderBook:
        bids: [] = []
        asks: [] = []

        bid = 65000
        ask = 66000
        delta = 1000
        for i in range(0,100):
            bids.append(OrderBookEntry(bid, 100))
            asks.append(OrderBookEntry(ask, 100))
            bid -= delta
            ask += delta

        bids.sort()
        bids.reverse()
        asks.sort()

        ob = OrderBook(self.instrument, "id1", bids, asks)
        return ob

    async def run(self):
        while Static.KeepRunning:
            await asyncio.sleep(20)
            self.timestamp = datetime.now()
            rnd = Decimal(random())
            for entry in self.ob.bids:
                entry.price = entry.price + rnd

            for entry in self.ob.asks:
                entry.price = entry.price + rnd

            await self.orderBookUpdateQueue.put("local Order book update")
        logging.error("Kill Switch Triggered")

    def initialize(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.run())


if __name__ == '__main__':
    instrument = "BTC_USDT"

    loop = asyncio.get_event_loop()

    localOrderBook = LocalOrderBook(instrument, asyncio.Queue())
    localOrderBook.initialize()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()



