import asyncio
import logging
from datetime import datetime

from sortedcontainers import SortedList
from decimal import Decimal

from core.Instrument import Instrument

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class OrderBookEntry:
    def __init__(self, price, amount):
        self.price: Decimal = Decimal(price)
        self.amount: str = amount

    def __eq__(self, other):
        return self.price == other.price

    def __str__(self):
        return '(%s, %s)' % (self.price, self.amount)

    def __lt__(self, other):
        return self.price < other.price


class OrderBook:
    def __init__(self, instrument: Instrument, last_id: id, bids: [], asks: []):
        self.instrument = instrument
        self.id = last_id
        self.asks = asks
        self.bids = bids


class LocalOrderBookBase:
    def __init__(self, instrument: Instrument, orderBookUpdateQueue: asyncio.Queue):
        self.instrument = instrument
        self.orderBookUpdateQueue = orderBookUpdateQueue
        self.ob = OrderBook(self.instrument, 0, asks=SortedList(), bids=SortedList())
        self.timestamp: datetime = datetime.now()

    @property
    def midTob(self):
        return Decimal(0.5) * (self.ob.bids[0].price + self.ob.asks[0].price)
