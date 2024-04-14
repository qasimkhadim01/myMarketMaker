from datetime import datetime
from decimal import Decimal

from core.Instrument import Coin, Instruments, Instrument
from core.MyEnums import OrderSide
from core.Orders import TickEvent


class MarketCache:
    _cache = {}

    def __init__(self, coins: [], pnlCurrency: Coin):
        self.pnlCurrency = pnlCurrency
        [MarketCache._cache.update({coin: TickEvent(datetime.now(),
                                                    Instruments.instruments.get(Instrument(Coin.BTC, Coin.USDT)),
                                                    Decimal(1.0), Decimal(1.0))}) for coin in coins]

        MarketCache._cache[Coin.USDT] = TickEvent(datetime.now(),
                                                  Instruments.instruments.get(Instrument(Coin.USDT, Coin.USDT)),
                                                  Decimal(1.0), Decimal(1.0))

    @staticmethod
    def getPrice(coin: Coin, amount: Decimal, orderSide: OrderSide):
        if orderSide == OrderSide.Buy:
            return MarketCache._cache.get(coin).askPrice
        else:
            return MarketCache._cache.get(coin).bidPrice

    @staticmethod
    def getMidPrice(coin: Coin, amount: Decimal):
        return MarketCache._cache.get(coin).midPrice

    def onTickEvent(tickEvent: TickEvent):
        MarketCache._cache[tickEvent.instrument.base] = tickEvent
