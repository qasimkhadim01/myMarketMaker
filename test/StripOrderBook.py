from connectivity.LocalOrderBookBase import OrderBookEntry
from decimal import Decimal

marketBids = [OrderBookEntry(1, 100)
                ,OrderBookEntry(2, 100)
                ,OrderBookEntry(3, 100)
                ,OrderBookEntry(8, 100)
                ,OrderBookEntry(5, 100)
                ,OrderBookEntry(6, 100)
                ,OrderBookEntry(7, 100) ]
myBids = [OrderBookEntry(8, 200),OrderBookEntry(2, 20)]
matches = [i for i, item in enumerate(marketBids) if
           item.price in [x.price for x in myBids]]


for i in range(len(matches)):
    marketBids[matches[i]].amount -= myBids[i].amount

marketBids = [x for x in marketBids if Decimal(x.amount) > 0.0]
print ('done')
