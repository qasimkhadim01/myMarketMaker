import asyncio
import logging
from datetime import datetime
from enum import Enum

from sortedcontainers import SortedList
from decimal import Decimal

import Static
from core.Instrument import Instrument

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
Static.appLoggers.append(logger)

class OrderBookEntry:

    def __init__(self, price, amount):
        self.price: Decimal = Decimal(price)
        self.amount: Decimal = Decimal(amount)

    def __eq__(self, other):
        return self.price == other.price

    def __str__(self):
        return '(%s, %s)' % (self.price, self.amount)

    def __lt__(self, other):
        return self.price < other.price


class OrderBook:
    def __init__(self, instrument: Instrument, last_id: id, asks: SortedList[OrderBookEntry], bids: SortedList[OrderBookEntry]):
        self.instrument = instrument
        self.id = last_id
        self.asks: SortedList[OrderBookEntry] = asks
        self.bids: SortedList[OrderBookEntry] = bids

    @classmethod
    def update_entry(cls, book: SortedList, entry: OrderBookEntry, sumAmount=False):
        if entry.amount == Decimal('0'):
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
                if sumAmount:
                    book[idx].amount += entry.amount
                else:
                    book[idx].amount = entry.amount

            return book.index(entry)
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


class LocalOrderBookBase:
    def __init__(self, instrument: Instrument, localOrderBookUpdateQueue: asyncio.Queue):
        self.instrument = instrument
        self.ob: OrderBook = OrderBook(self.instrument, 0, asks=SortedList(), bids=SortedList())
        self.localOrderBookUpdateQueue = localOrderBookUpdateQueue
        self.obTimeStamp: datetime = datetime.now()
        self.topOfBookBid:OrderBookEntry = OrderBookEntry(0,0)
        self.topOfBookAsk:OrderBookEntry = OrderBookEntry(0, 0)
        self.tobTimeStamp = datetime.now()


    @property
    def midTob(self):
        return Decimal(0.5) * (self.ob.bids[0].price + self.ob.asks[0].price)

    def initialize(self):
        pass