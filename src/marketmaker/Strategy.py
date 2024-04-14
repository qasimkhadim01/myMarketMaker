from enum import Enum

class Strategy(Enum):
    Best = "best"
    Join = "join"
    Defensive = "defensive"
    Depth = 1
    RiskLimit=1250

class SpreadMatrix(Enum):
    MinSpread = 1
    MaxSpread = 5

class OrderSizeInDollar:
    sizes = [100,200,300]

