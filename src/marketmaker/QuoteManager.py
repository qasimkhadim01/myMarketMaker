import Static
from connectivity.gateio import Api
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from core.Orders import SpotLimitOrder
from core.MyEnums import OrderSide, OrderStatus
from marketmaker.Strategy import Strategy, OrderSizeInDollar
import logging

logger = logging.getLogger(__name__)


class QuoteManager:
    def __init__(self, strategy: Strategy, instrument: str, depth: Strategy.Depth, exchangeManager: ExchangeManagerBase):
        self.instrument = instrument
        self.strategy = strategy
        self.depth = depth
        self.exchangeManager = exchangeManager
        self.myBids = []
        self.myAsks = []

    @property
    def nextOrderId(self):
        orderId = "t-" + Api.subAccount + "_" + str(Static.orderCounter)
        Static.orderCounter += 1
        return orderId

    def initialize(self):
        if len(self.exchangeManager.localOrderBook.bids) > 0:
            bids = self.exchangeManager.localOrderBook.ob.bids[:self.depth.value]
            asks = self.exchangeManager.localOrderBook.ob.asks[:self.depth.value]

            for i in range(len(bids)):
                self.myBids.append(SpotLimitOrder(self.nextOrderId, self.instrument, OrderSide.Buy
                                                  , OrderSizeInDollar.sizes[i] / bids[i].price, bids[i].price))

            for i in range(len(asks)):
                self.myAsks.append(SpotLimitOrder(self.nextOrderId, self.instrument, OrderSide.Buy
                                                  , OrderSizeInDollar.sizes[i] / asks[i].price, asks[i].price))

            [self.exchangeManager.sendLimitOrder(order) for order in self.myBids if order.status == OrderStatus.New]
            [self.exchangeManager.sendLimitOrder(order) for order in self.myAsks if order.status == OrderStatus.New]


    async def updateQuotes(self):
        bids = self.exchangeManager.localOrderBook.ob.bids[:self.depth.value]
        asks = self.exchangeManager.localOrderBook.ob.asks[:self.depth.value]

        for i in range(len(bids)):
            if bids[i] != self.myBids[i]:
                self.myBids[i].status = OrderStatus.Amend
                self.myBids[i].price = bids[i].price

        for i in range(len(asks)):
            if asks[i] != self.myAsks[i]:
                self.myAsks[i].status = OrderStatus.Amend
                self.myAsks[i].price = asks[i].price
        logger.debug("generating updated Quotes")
        [self.exchangeManager.amendLimitOrder(order) for order in self.myBids if order.status == OrderStatus.Amend]
        [self.exchangeManager.amendLimitOrder(order) for order in self.myAsks if order.status == OrderStatus.Amend]

    async def run(self):
        while True:
            result = await self.exchangeManager.quotesQueue.get()
            print('here')
#            if result.get('s') != self.instrument:
#                continue

#            await self.updateQuotes()
