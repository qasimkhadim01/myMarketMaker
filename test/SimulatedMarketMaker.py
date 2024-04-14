import asyncio
import logging

import Static
from Test.SimulatedExchange import SimulatedExchange
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, Configuration
from marketmaker.Strategy import Strategy
from marketmaker.QuoteManager import QuoteManager


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s: %(message)s",
                    handlers=[logging.FileHandler(Static.logFile),
                              logging.StreamHandler()])
logger = logging.getLogger()

conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
instrument = "BTC_USDT"

exchangeManager = SimulatedExchange(instrument, conn)
quoteManager = QuoteManager(Strategy.Best, instrument, Strategy.Depth, exchangeManager)
quoteManager.initialize()
exchangeManager.initialize()

loop = asyncio.get_event_loop()
loop.create_task(quoteManager.run())
loop.create_task(exchangeManager.run())
loop.create_task(conn.run())

try:
    loop.run_forever()
except KeyboardInterrupt:
    for task in asyncio.Task.all_tasks(loop):
        task.cancel()
    loop.close()