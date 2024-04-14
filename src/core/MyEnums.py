from enum import Enum

class Role(Enum):
    Maker = "maker"
    Taker = "taker"

class OrderSide(Enum):
    Buy = "buy"
    Sell = "sell"

class OrderStatus(Enum):
    New = "new"
    Amend = "amended"
    Active = "active"
    Filled = "filled"
    Cancelled = "cancelled"
