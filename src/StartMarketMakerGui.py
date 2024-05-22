import asyncio
import logging
from typing import List

from sortedcontainers import SortedList

import Static
from decimal import Decimal

from connectivity.ExchangeManagerBase import ExchangeManagerBase
from marketmaker.KillSwitch import KillSwitch
from marketmaker.MarketMakerGui import MarketMakerGui
from connectivity.LocalOrderBookBase import LocalOrderBookBase, OrderBookEntry, OrderBook
from connectivity.gateio import Api
from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Coin, Instruments, Instrument
from marketmaker.RiskManager import RiskManager
from marketmaker.Strategy import Strategy,  GlobalRiskLimit
from marketmaker.QuoteManager import QuoteManager

logging.basicConfig(level=logging.ERROR, format=Static.LOGFORMAT,
                    handlers=[logging.FileHandler(Static.logFile, mode='w'),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Static.appLoggers.append(logger)

async def dummyTrade(instrument:Instrument, rm: RiskManager, exchangeManager: ExchangeManagerBase):
    await asyncio.sleep(30)
    amount: Decimal = GlobalRiskLimit
    amount = amount + 100
    midPrice = exchangeManager.localOrderBooks[instrument].midTob
    RiskManager.risks[Coin.UX].positionValue = amount
    RiskManager.risks[Coin.UX].position = Decimal(amount/midPrice)


if __name__ == '__main__':
    logger.info("starting up")
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY, max_retry=1000))
    instruments:List[Instrument] = list()
    instrument = Instruments.instruments.get(str(Instrument(Coin.UX, Coin.USDT)))
    instruments.append(Instruments.instruments.get(str(Instrument(Coin.UX, Coin.USDT))))

    pnlCoin = Coin.USDT
    coins = [instrument.base]

    exchangeManager = GateIOManager(instruments, conn)
    quoteManager = QuoteManager(instrument, exchangeManager)
    rmLocalOrderBooks = {}
    [rmLocalOrderBooks.update({coin: exchangeManager.localOrderBooks[   Instruments.instruments.get(str(Instrument(coin, Coin.USDT)))]}) for coin in coins]
    usdtLocalOrderBook = LocalOrderBookBase(instrument, None)
    bids:SortedList = SortedList(key=lambda x: -x.price)
    bids.add(OrderBookEntry(1, 100000))
    asks:SortedList = SortedList()
    asks.add(OrderBookEntry(1, 100000))
    usdtLocalOrderBook.ob = OrderBook(instrument, "id1", bids, asks)
    rmLocalOrderBooks[Coin.USDT] = usdtLocalOrderBook

    rm: RiskManager = RiskManager(coins, pnlCoin, rmLocalOrderBooks)

    quoteManager.initialize()
    exchangeManager.initialize()

    loop = asyncio.get_event_loop()
    killSwitch: KillSwitch = KillSwitch(loop)
    loop.create_task(quoteManager.run())
    loop.create_task(exchangeManager.run())
    loop.create_task(exchangeManager.runMyOrderUpdate())
    loop.create_task(conn.run())
    loop.create_task(killSwitch.run())

    #loop.create_task(dummyTrade(instrument, rm, exchangeManager))
    marketMakerGui: MarketMakerGui = MarketMakerGui(loop, quoteManager)
    loop.run_forever()
    loop.close()
