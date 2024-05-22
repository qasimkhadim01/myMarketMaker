import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from random import  randint
from typing import Dict

from sortedcontainers import SortedList

import Static
from connectivity.LocalOrderBookBase import LocalOrderBookBase, OrderBookEntry, OrderBook
from core.Instrument import Instrument, Instruments
from core.MyEnums import OrderSide
from core.Orders import SpotLimitOrder

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



class SimulatedLocalOrderBook(LocalOrderBookBase):
    def __init__(self, instrument: Instrument, localOrderBookUpdateQueue: asyncio.Queue):
        super().__init__(instrument, localOrderBookUpdateQueue)
        self.q = asyncio.Queue()
        loop = asyncio.get_event_loop()
        self.myOb: Dict[str, SpotLimitOrder] = dict()
        self.publicOb: OrderBook = loop.run_until_complete(self.construct_base_order_book())
        self.ob: OrderBook = loop.run_until_complete(self.construct_base_order_book())
        self.topOfBookBid = self.ob.bids[0]
        self.topOfBookAsk = self.ob.asks[0]

        self.counter = 0

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
        bids: SortedList = SortedList(key=lambda x: -x.price)
        asks: SortedList = SortedList()

        bid = 0.002865
        ask = 0.002881
        delta = 0.000001
        for i in range(0,100):
            bids.add(OrderBookEntry(round(bid, self.instrument.pricePrecision), Decimal(100)))
            asks.add(OrderBookEntry(round(ask, self.instrument.pricePrecision), Decimal(100)))
            bid -= delta
            ask += delta

        #reversed(bids)

        ob = OrderBook(self.instrument, "id1", asks, bids)
        return ob

    async def runTopOfBook(self):
        priceUpdate = 5
        counter = 0
        while Static.KeepRunning:
            await asyncio.sleep(5)
            counter += 1
            if counter % priceUpdate == 0:
                change = round(Decimal(randint(0, 5) / (10 ** self.instrument.pricePrecision)), self.instrument.pricePrecision)
                self.topOfBookBid.price = self.publicOb.bids[0].price + change
                self.topOfBookAsk.price = self.publicOb.asks[0].price + change
            else:
                change = round(Decimal(randint(1, 10) / (10 ** self.instrument.amountPrecision)), self.instrument.amountPrecision)
                self.topOfBookBid.amount = self.publicOb.bids[0].amount + change
                self.topOfBookAsk.amount = self.publicOb.asks[0].amount+ change


            self.tobTimeStamp = datetime.now()
            logger.debug(f"Top of book is {round(self.topOfBookBid.price, self.instrument.pricePrecision)} {round(self.topOfBookAsk.price, self.instrument.pricePrecision)}")
            logger.debug(f"counter is {counter}")
            await self.localOrderBookUpdateQueue.put("Top of Book update")


    async def run(self):
        while Static.KeepRunning:
            await asyncio.sleep(10)

            change = round(Decimal(1 / (10 ** self.instrument.pricePrecision)),
                           self.instrument.pricePrecision)

            for i in range(len(self.publicOb.bids)):
                if i == 0:
                    self.publicOb.bids[i].price = round(self.topOfBookBid.price, self.instrument.pricePrecision)
                else:
                    self.publicOb.bids[i].price = round(self.publicOb.bids[i-1].price - change, self.instrument.pricePrecision)

            for i in range(len(self.publicOb.asks)):
                if i == 0:
                    self.publicOb.asks[i].price = round(self.topOfBookAsk.price, self.instrument.pricePrecision)
                else:
                    self.publicOb.asks[i].price = round(self.publicOb.asks[i-1].price + change, self.instrument.pricePrecision)

            self.buildOrderBook()
            self.obTimeStamp = datetime.now()
            #await self.localOrderBookUpdateQueue.put("local Order book update")


    def buildOrderBook(self):
        self.ob.bids.clear()
        self.ob.asks.clear()
        [self.ob.update_entry(self.ob.bids, OrderBookEntry(round(order.price, self.instrument.pricePrecision), order.amount), True) for order in self.publicOb.bids]
        [self.ob.update_entry(self.ob.asks, OrderBookEntry(round(order.price, self.instrument.pricePrecision), order.amount), True) for order in self.publicOb.asks]
        [self.ob.update_entry(self.ob.bids, OrderBookEntry(round(order.price, self.instrument.pricePrecision), order.amount), True) for order in self.myOb.values() if order.side == OrderSide.Buy]
        [self.ob.update_entry(self.ob.asks, OrderBookEntry(round(order.price, self.instrument.pricePrecision), order.amount), True) for order in self.myOb.values() if order.side == OrderSide.Sell]

    def initialize(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.run())
        loop.create_task(self.runTopOfBook())



if __name__ == '__main__':
    instrument = Instruments.instruments["UMEE_USDT"]

    loop = asyncio.get_event_loop()

    localOrderBook = SimulatedLocalOrderBook(instrument, asyncio.Queue())
    localOrderBook.initialize()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()



