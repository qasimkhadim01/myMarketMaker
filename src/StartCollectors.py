import asyncio
import logging
import Static
from connectivity.gateio import Api
from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio.LocalOrderBook import LocalOrderBook
from connectivity.gateio.ws import Configuration, Connection
from core.Instrument import Instruments
from tickcollector.OrderBookCollector import OrderBookCollector

logging.basicConfig(level=logging.ERROR, format="%(asctime)s: %(message)s")
logger = logging.getLogger()

conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
instrument = Instruments.instruments.get("BTC_USDT")
exchangeManager = GateIOManager(str(instrument), conn)
exchangeManager.initialize()
orderBookCollector = OrderBookCollector(Static.gateioCollectorFile, exchangeManager)




loop = asyncio.get_event_loop()
loop.create_task(orderBookCollector.update())
loop.create_task(exchangeManager.run())
loop.create_task(conn.run())

try:
    loop.run_forever()
except KeyboardInterrupt:
    for task in asyncio.Task.all_tasks(loop):
        task.cancel()
    loop.close()