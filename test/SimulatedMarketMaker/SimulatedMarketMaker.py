import asyncio
import logging
from sortedcontainers import SortedList
import Static
from Test.SumulatedMarketMaker.SimulatedExchange import SimulatedExchange
from connectivity.LocalOrderBookBase import LocalOrderBookBase, OrderBookEntry, OrderBook
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Coin, Instruments
from marketmaker.RiskManager import RiskManager
from marketmaker.Strategy import Strategy, BestStrategy
from marketmaker.QuoteManager import QuoteManager

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT,
                    handlers=[logging.FileHandler(Static.logFile, mode='w'),
                              logging.StreamHandler()])
logger = logging.getLogger()

conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
instrument = Instruments.instruments.get("BTC_USDT")
pnlCoin = Coin.USDT
coins = [instrument.base]

exchangeManager = SimulatedExchange(instrument, conn)
quoteManager = QuoteManager(instrument,  exchangeManager)
localOrderBooks = {}
[localOrderBooks.update({coin: exchangeManager.localOrderBook}) for coin in coins]
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