from enum import Enum


class RiskParam(Enum):
    Depth = 20
    RiskLimit = 125

class Strategy:
    nLevels = 1
    pass

class BestStrategy(Strategy):
    level = -1
    offset = 1

class JoinStrategy(Strategy):
    level = 0

class DefensiveStrategy(Strategy):
    level = 2

class MultiLadderStrategy(Strategy):
    startLevel = 2
    nLevels = 4


class MultiRandomStrategy(Strategy):
    startLevel = 2
    nLevels = 3
    offsetMin = 10
    offsetMax = 20

class SpreadMatrix(Enum):
    MinSpread = 1
    MaxSpread = 5


class OrderSizeInDollar:
    sizes = [100]

class Touched(Enum):
    Static = "Static"
    Refresh = "Refresh"


liveStrategies: [] = [JoinStrategy(), MultiLadderStrategy()]
TOUCHED = Touched.Static
