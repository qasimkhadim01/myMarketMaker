import asyncio
import copy
from decimal import Decimal

from sortedcontainers import SortedList

from OrderManager import orderList
from connectivity.gateio import Api
from connectivity.gateio.LocalOrderBook import LocalOrderBook
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Instruments
from core.MyEnums import OrderSide
from core.Orders import SpotLimitOrder


def strippedOrderBook(localOrderBook, myBids, myAsks):
    marketBids = copy.deepcopy(localOrderBook.ob.bids[:20])
    marketAsks = copy.deepcopy(localOrderBook.ob.asks[:20])
    bidsAsList = list(myBids.values())
    asksAsList = list(myAsks.values())

    matches = [i for i, item in enumerate(marketBids) if
               item.price in [x.price for x in bidsAsList]]

    for i in range(len(matches)):
        marketBids[matches[i]].amount -= bidsAsList[i].amount
    marketBids = [x for x in marketBids if Decimal(x.amount) > 0.0]

    matches = [i for i, item in enumerate(marketAsks) if
               item.price in [x.price for x in asksAsList]]

    for i in range(len(matches)):
        marketAsks[matches[i]].amount -= asksAsList[i].amount

    marketAsks = [x for x in marketAsks if x.amount > 0.0]
    return SortedList(marketBids, key=lambda x: -x.price), SortedList(marketAsks)


if __name__ == '__main__':
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    instrument = Instruments.instruments["UMEE_USDT"]
    loop = asyncio.get_event_loop()
    localOrderBook = LocalOrderBook(instrument, conn, asyncio.Queue())
    orders = orderList()
    myBids:dict[str, SpotLimitOrder] = dict()
    myAsks: dict[str, SpotLimitOrder] = dict()

    [myBids.update({order.id: order})  for order in orders if order.side == OrderSide.Buy]
    [myAsks.update({order.id: order}) for order in orders if order.side == OrderSide.Sell]

    bids, asks = strippedOrderBook(localOrderBook, myBids, myAsks)
    print ('done')



