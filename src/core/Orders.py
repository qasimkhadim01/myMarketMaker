from datetime import datetime
from decimal import Decimal

from core.Instrument import Instrument
from core.MyEnums import OrderSide, OrderStatus, Role


class Order:
    def __init__(self, id: str, instrument: Instrument, side: OrderSide, amount: Decimal, price: Decimal):
        self.timestamp = datetime.now()
        self.id = id
        self.instrument = instrument
        self.side = side
        self.amount = amount
        self.price = Decimal(price)
        self.status = OrderStatus.New

    def __eq__(self, other):
        return self.price == other.price and self.side == other.side

    def __str__(self):
        return '(id=%s, instrument=%s, price=%s, amount=%s, %s)' % (self.id, self.instrument, self.price, self.amount, self.side)


class SpotLimitOrder(Order):
    def __init__(self, id: str, instrument: Instrument, side: OrderSide, amount: Decimal, price: Decimal):
        super().__init__(id, instrument, side, amount, Decimal(price))


class SpotMarketOrder(Order):
    def __init__(self, id: str, instrument: Instrument, side: OrderSide, amount: Decimal, price: Decimal):
        super().__init__(id, instrument, side, amount, Decimal(price))  # price must be marketPrice.

class FilledOrder(Order):
    def __init__(self, id: str, instrument: Instrument, side: OrderSide, filledAmount: Decimal, filledPrice: Decimal, role: Role):
        super().__init__(id, instrument, side, filledAmount, Decimal(filledPrice))
        self.status = OrderStatus.Filled
        self.role = role

    def getSignedAmount(self):
        return self.amount if self.side == OrderSide.Buy else self.amount*-1

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
        return (self.bidPrice + self.askPrice)/Decimal(2.0)
