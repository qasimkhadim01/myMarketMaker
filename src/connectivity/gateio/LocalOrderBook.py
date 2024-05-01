import asyncio
import itertools
import logging
import typing
from datetime import datetime
from decimal import Decimal

import aiohttp
from sortedcontainers import SortedList

import Static
from connectivity.LocalOrderBookBase import LocalOrderBookBase
from connectivity.gateio import Api
from connectivity.gateio.ws import Configuration, Connection, WebSocketResponse
from connectivity.gateio.ws.Spot import SpotOrderBookUpdateChannel
from core.Instrument import Instrument, Instruments
from marketmaker.Strategy import Strategy, RiskParam

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

class SimpleRingBuffer(object):
    def __init__(self, size: int):
        self.max = size
        self.data = []
        self.cur = 0

    class __Full:
        # to avoid warning hints from IDE
        max: int
        data: typing.List
        cur: int

        def append(self, x):
            self.data[self.cur] = x
            self.cur = (self.cur + 1) % self.max

        def __iter__(self):
            for i in itertools.chain(range(self.cur, self.max), range(self.cur)):
                yield self.data[i]

        def get(self, idx):
            return self.data[(self.cur + idx) % self.max]

        def __getitem__(self, item):
            if isinstance(item, int):
                return self.get(item)
            return (self.data[self.cur:] + self.data[:self.cur]).__getitem__(item)

        def __len__(self):
            return self.max
        # end of class __Full

    def __iter__(self):
        for i in self.data:
            yield i

    def append(self, x):
        self.data.append(x)
        if len(self.data) == self.max:
            self.cur = 0
            # Permanently change self's class from non-full to full
            self.__class__ = self.__Full

    def get(self, idx):
        return self.data[idx]

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __len__(self):
        return len(self.data)


class OrderBookEntry:
    def __init__(self, price, amount):
        self.price: Decimal = Decimal(price)
        self.amount: str = amount

    def __eq__(self, other):
        return self.price == other.price

    def __str__(self):
        return '(%s, %s)' % (self.price, self.amount)


class OrderBook:
    def __init__(self, instrument: Instrument, last_id: id, asks: SortedList, bids: SortedList):
        self.instrument = instrument
        self.id = last_id
        self.asks = asks
        self.bids = bids

    @classmethod
    def update_entry(cls, book: SortedList, entry: OrderBookEntry):
        if Decimal(entry.amount) == Decimal('0'):
            # remove price if amount is 0
            try:
                book.remove(entry)
            except ValueError:
                pass
        else:
            try:
                idx = book.index(entry)
            except ValueError:
                # price not found, insert it
                book.add(entry)
            else:
                # price found, update amount
                book[idx].amount = entry.amount

    def __str__(self):
        return '\n  id: %d\n  asks:\n%s\n  bids:\n%s' % (self.id,
                                                         '\n'.join([' ' * 4 + str(a) for a in self.asks]),
                                                         '\n'.join([' ' * 4 + str(b) for b in self.bids]))

    def update(self, ws_update):
        if ws_update['u'] < self.id + 1:
            # ignore older message
            return
        if ws_update['U'] > self.id + 1:
            raise ValueError("base order book ID %d falls behind update between %d-%d" %
                             (self.id, ws_update['U'], ws_update['u']))
        # start from the first message which satisfies U <= ob.id+1 <= u
        logger.debug("current id %d, update from %s", self.id, ws_update)
        for ask in ws_update['a']:
            entry = OrderBookEntry(*ask)
            self.update_entry(self.asks, entry)
        for bid in ws_update['b']:
            entry = OrderBookEntry(*bid)
            self.update_entry(self.bids, entry)
        # update local order book ID
        # check order book overlapping
        if len(self.asks) > 0 and len(self.bids) > 0:
            if self.asks[0].price <= self.bids[0].price:
                raise ValueError("price overlapping, min ask price %s not greater than max bid price %s" % (
                    self.asks[0].price, self.bids[0].price))
        self.id = ws_update['u']


class LocalOrderBook(LocalOrderBookBase):
    def __init__(self, instrument: Instrument, conn: Connection, orderBookUpdateQueue: asyncio.Queue):
        super().__init__(instrument, orderBookUpdateQueue)
        self.conn = conn
        self.instrument = instrument
        self.q = asyncio.Queue()
        self.orderBookUpdateQueue = orderBookUpdateQueue
        self.buf = SimpleRingBuffer(size=500)
        self.ob = OrderBook(self.instrument, 0, asks=SortedList(), bids=SortedList())
        loop = asyncio.get_event_loop()
        self.ob = loop.run_until_complete(self.construct_base_order_book())

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
        while True:
            async with aiohttp.ClientSession() as session:
                # aiohttp does not allow boolean parameter variable
                async with session.get('https://api.gateio.ws/api/v4/spot/order_book',
                                       params={'currency_pair': str(self.instrument), 'limit': RiskParam.Depth.value,
                                               'with_id': 'true'}) as response:
                    if response.status != 200:
                        logger.warning("failed to retrieve base order book: ", await response.text())
                        await asyncio.sleep(1)
                        continue
                    result = await response.json()
                    assert isinstance(result, dict)
                    assert result.get('id')
                    logger.debug("retrieved new base order book with id %d", result.get('id'))
                    ob = OrderBook(self.instrument, result.get('id'),
                                   SortedList([OrderBookEntry(*x) for x in result.get('asks')], key=lambda x: x.price),
                                   # sort bid from high to low
                                   SortedList([OrderBookEntry(*x) for x in result.get('bids')], key=lambda x: -x.price))
            # use cached result to recover our local order book fast
            for b in self.buf:
                try:
                    ob.update(b)
                except ValueError as e:
                    logger.warning("failed to update: %s", e)
                    await asyncio.sleep(0.5)
                    break
            else:
                return ob

    async def run(self):
        while Static.KeepRunning:
            self.ob = await self.construct_base_order_book()
            while Static.KeepRunning:
                result = await self.q.get()  # from websocket
                try:
                    self.ob.update(result)
                    #await self.orderBookUpdateQueue.put(result)
                except ValueError as e:
                    logger.error("failed to update: %s", e)
                    # reconstruct order book
                    break
        logging.error("Kill Switch Triggered")


    def _cache_update(self, ws_update):
        if len(self.buf) > 0:
            last_id = self.buf[-1]['u']
            if ws_update['u'] < last_id:
                # ignore older message
                return
            if ws_update['U'] != last_id + 1:
                # update message not consecutive, reconstruct cache
                self.buf = SimpleRingBuffer(size=100)
        self.buf.append(ws_update)

    async def ws_callback(self, conn: Connection, response: WebSocketResponse):
        if response.error:
            # stop the client if error happened
            conn.close()
            raise response.error
        # ignore subscribe success response
        if 's' not in response.result or response.result.get('s') != str(self.instrument):
            return
        result = response.result
        logger.debug("received update: %s", result)
        assert isinstance(result, dict)
        self._cache_update(result)
        self.timestamp = datetime.now()
        await self.q.put(result)

    def initialize(self):
        self.channel = SpotOrderBookUpdateChannel(self.conn, self.ws_callback)
        self.channel.subscribe([str(self.instrument), "100ms"])

        loop = asyncio.get_event_loop()
        self.ob = loop.run_until_complete(self.construct_base_order_book())
        loop.create_task(self.run())


    def release(self):
        self.channel.unsubscribe([str(self.instrument), "100ms"])
        self.conn.unregister(self.channel.unsubscribe())

if __name__ == '__main__':
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    instrument = Instruments.instruments["BTC_USDT"]

    loop = asyncio.get_event_loop()

    localOrderBook = LocalOrderBook(instrument, conn, asyncio.Queue())
    localOrderBook.initialize()

    loop.create_task(localOrderBook.run())
    loop.create_task(conn.run())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()


