from collections import namedtuple
from enum import Enum


class Side(Enum):
    Left = "Left"
    Right = "Right"

    def __init__(self):
        self.side = Side.Left

    def other(self):
        if self.side == Side.Left:
            return Side.Right
        elif self.side == Side.Right:
            return Side.Left


Pair = namedtuple('Pair', ['Left', 'Side'])
