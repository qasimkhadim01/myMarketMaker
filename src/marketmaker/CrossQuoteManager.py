from sortedcontainers import SortedList

from connectivity.ExchangeManagerBase import ExchangeManagerBase
from connectivity.LocalOrderBookBase import OrderBookEntry
from core.Instrument import Instrument
from marketmaker.QuoteManager import QuoteManager
from marketmaker.Strategy import Strategy


class CrossQuoteManager(QuoteManager):
    def __init__(self, instrument: Instrument, legs:tuple, exchangeManager: ExchangeManagerBase):
        super().__init__(instrument, exchangeManager)
        self.legs = legs

    def buildStrategy(self, strategy: Strategy, obBids:SortedList[OrderBookEntry], obAsks:SortedList[OrderBookEntry]):
        leg1StrippedOrderBook = self.exchangeManager.localOrderBooks