import asyncio
import logging
from typing import List

import Static
from Test.SumulatedMarketMaker.SimulatedExchange import SimulatedExchange
from connectivity.LocalOrderBookBase import LocalOrderBookBase, OrderBookEntry, OrderBook
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Coin, Instruments, Instrument
from marketmaker.RiskManager import RiskManager
from marketmaker.QuoteManager import QuoteManager

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT,
                    handlers=[logging.FileHandler(Static.logFile, mode='w'),
                              logging.StreamHandler()])
logger = logging.getLogger()

conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
instruments: List[Instrument] = list()
instrument = Instruments.instruments["UMEE_USDT"]
instruments.append(instrument)

pnlCoin = Coin.USDT
coins = [instrument.base]

exchangeManager = SimulatedExchange(instrument, conn)
quoteManager = QuoteManager(instrument,  exchangeManager)
localOrderBooks = {}
[localOrderBooks.update({instrument.base: exchangeManager.localOrderBooks[instrument]}) for instrument in instruments]
usdtLocalOrderBook = LocalOrderBookBase(instrument, None)
bids = []
bids.append(OrderBookEntry(1, 100000))
asks = []
asks.append(OrderBookEntry(1, 100000))
usdtLocalOrderBook.ob = OrderBook(instrument, "id1", bids, asks)
localOrderBooks[Coin.USDT] =  usdtLocalOrderBook

rm: RiskManager = RiskManager(coins, pnlCoin, localOrderBooks)
quoteManager.initialize()
exchangeManager.initialize()

loop = asyncio.get_event_loop()
loop.create_task(quoteManager.run())
loop.create_task(exchangeManager.run())
loop.create_task(exchangeManager.runMyOrderUpdate())
loop.create_task(conn.run())

try:
    loop.run_forever()
except KeyboardInterrupt:
    for task in asyncio.Task.all_tasks(loop):
        task.cancel()
    loop.close()