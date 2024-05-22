import copy
from decimal import Decimal
from typing import Dict, List

from connectivity.LocalOrderBookBase import OrderBookEntry
from core.Instrument import Instruments
from core.MyEnums import OrderSide
from core.Orders import SpotLimitOrder, Order
from marketmaker.Strategy import BestStrategy

instrument = Instruments.instruments["UMEE_USDT"]
strategy = BestStrategy()
myBids:Dict[str, SpotLimitOrder] = dict()
myAsks:Dict[str, SpotLimitOrder] = dict()

#inital Orders
bidOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), instrument, OrderSide.Buy
                                          , Decimal(38314.176245), Decimal(0.002610), strategy)
myBids.update({bidOrder.id: bidOrder})
askOrder: SpotLimitOrder = SpotLimitOrder(Order.nextOrderId(), instrument, OrderSide.Sell
                                              , Decimal(37850.113550), Decimal(0.002642), strategy)
myAsks.update({askOrder.id: askOrder})

gTopOfBookBid:OrderBookEntry = OrderBookEntry(round(Decimal(0.002611), instrument.pricePrecision), round(Decimal(10364.7), instrument.amountPrecision))
gTopOfBookAsk:OrderBookEntry = OrderBookEntry(round(Decimal(0.002625), instrument.pricePrecision), round(Decimal(6673.54077742), instrument.amountPrecision))


def strippedBest():
    topOfBookBid = copy.deepcopy(gTopOfBookBid)
    topOfBookAsk = copy.deepcopy(gTopOfBookAsk)

    myBestBid = [i for i in myBids.values() if isinstance(i.strategy, BestStrategy)]
    myBestAsk = [i for i in myAsks.values() if isinstance(i.strategy, BestStrategy)]
    if len(myBestBid) > 0 and myBestBid[0].price == topOfBookBid.price:
        topOfBookBid.amount -= myBestBid[0].amount
    if len(myBestAsk) > 0 and myBestAsk[0].price == topOfBookAsk.price:
        topOfBookAsk.amount -= myBestAsk[0].amount

    return topOfBookBid, topOfBookAsk


def buildStrategy():
    bids: List[Decimal] = list()
    asks: List[Decimal] = list()

    strippedBestBid, strippedBestAsk = strippedBest()
    if strippedBestBid.amount <=0:
        strategyBid = strippedBestBid.price
    else:
        strategyBid = round(strippedBestBid.price + Decimal(BestStrategy.spreadOffset / (10 ** instrument.pricePrecision))
                  , instrument.pricePrecision)
    if strippedBestAsk.amount <=0:
        strategyAsk = strippedBestAsk.price
    else:
        strategyAsk = round(strippedBestAsk.price - Decimal(BestStrategy.spreadOffset/(10**instrument.pricePrecision))
                          ,instrument.pricePrecision)
    marketSpread = (strategyAsk -strategyBid)*10**instrument.pricePrecision
    if marketSpread > BestStrategy.minSpread:
        bids.append(strategyBid)
        asks.append(strategyAsk)
    else:
        bids.append(strippedBestBid.price)
        asks.append(strippedBestAsk.price)

    return bids, asks


bids, asks = buildStrategy()
myBids[bidOrder.id].price = bids[0]
myAsks[askOrder.id].price = asks[0]

gTopOfBookBid.price = Decimal(0.002611)
gTopOfBookBid.amount =  Decimal(10364.7)
gTopOfBookAsk.price = Decimal(0.002642)
gTopOfBookAsk.amount =  Decimal(37850.1)

bids, asks = buildStrategy()
myBids[bidOrder.id].price = bids[0]
myAsks[askOrder.id].price = asks[0]


gTopOfBookBid.price = Decimal(0.002612)
gTopOfBookBid.amount =  Decimal(38314.1)
gTopOfBookAsk.price = Decimal(0.002642)
gTopOfBookAsk.amount =  Decimal(37850.1)

bids, asks = buildStrategy()
myBids[bidOrder.id].price = bids[0]
myAsks[askOrder.id].price = asks[0]

print('done')






