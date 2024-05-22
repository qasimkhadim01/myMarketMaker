import logging
from datetime import datetime
from decimal import Decimal
import time
from connectivity.gateio import Api
from core.Instrument import Instrument
from core.MyEnums import OrderSide, OrderStatus, Role
from marketmaker.Strategy import Strategy

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Order:
    orderCounter = 0

    def __init__(self, id: str, instrument: Instrument, side: OrderSide, amount: Decimal, price: Decimal):
        self.timestamp = datetime.now()
        self.id = id
        self.instrument = instrument
        self.side = side
        self.amount = amount
        self.price = Decimal(round(price, self.instrument.pricePrecision))
        self.status = OrderStatus.New
        self.filledAmount = 0
        self.strategy:Strategy = None
        self.creationTime = int(time.time())
        self.completionTime =int(time.time())
        self.updateTime = int(time.time())

    def __eq__(self, other):
        return self.price == other.price and self.side == other.side

    def __str__(self):
        return (f"{self.timestamp.strftime('%H:%M:%S')},id={self.id}, {str(self.instrument)}, price={self.price:.{self.instrument.pricePrecision}f}, amount={self.amount:.{self.instrument.amountPrecision}f}"
                f", filledAmount={self.filledAmount:.{self.instrument.amountPrecision}f}, {self.side}, {self.status}, {self.strategy.__class__.__name__}, {self.__class__.__name__}, updateTime={time.ctime(self.updateTime)}")
    @staticmethod
    def nextOrderId() -> str:
        orderId = "t-" + Api.subAccount + "_" + str(Order.orderCounter)
        Order.orderCounter += 1
        return orderId


class SpotLimitOrder(Order):
    def __init__(self, id: str, instrument: Instrument, side: OrderSide, amount: Decimal, price: Decimal, strategy: Strategy):
        super().__init__(id, instrument, side, amount, Decimal(price))
        self.strategy = strategy
class SpotMarketOrder(Order):
    def __init__(self, id: str, instrument: Instrument, side: OrderSide, amount: Decimal, price: Decimal):
        super().__init__(id, instrument, side, amount, Decimal(price))  # price must be marketPrice.


class FilledOrder(Order):
    def __init__(self, id: str, instrument: Instrument, side: OrderSide, filledAmount: Decimal, filledPrice: Decimal,
                 role: Role):
        super().__init__(id, instrument, side, filledAmount, Decimal(filledPrice))
        self.status = OrderStatus.Filled
        self.role = role
        self.filledAmount = filledAmount

    def getSignedAmount(self):
        return self.amount if self.side == OrderSide.Buy else self.amount * -1

    def getQuoteSignedAmount(self):
        return self.price * self.amount * -1 if self.side == OrderSide.Buy else self.price * self.amount


class TickEvent:
    def __init__(self, timestamp: datetime, instrument: Instrument, bidPrice: Decimal, askPrice: Decimal):
        self.timestamp = timestamp
        self.instrument = instrument
        self.bidPrice = bidPrice
        self.askPrice = askPrice

    @property
    def midPrice(self):
        return (self.bidPrice + self.askPrice) / Decimal(2.0)
