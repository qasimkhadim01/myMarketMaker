import asyncio
import logging
from typing import List

import Static
from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Instruments
from core.MyEnums import OrderSide
from core.Orders import SpotLimitOrder, SpotMarketOrder
from decimal import Decimal

from marketmaker.Strategy import Strategy, DefensiveStrategy

if __name__ == '__main__':
    FORMAT = "[%(asctime)s:%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT,
                        handlers=[logging.FileHandler(Static.logFile, mode='w'),
                                  logging.StreamHandler()])
    logger = logging.getLogger()

    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    sInstrument = "UMEE_USDT"
    instrument = Instruments.instruments[sInstrument]
    amount = Decimal(1000)
    price = Decimal(0.002956)
    price1 = Decimal(0.002950)
    orderSide = OrderSide.Buy

    # exchangeManager = SimulatedExchange(instrument, conn)
    exchangeManager = GateIOManager(instrument, conn)
    exchangeManager.initialize()

    loop = asyncio.get_event_loop()
    exchangeManager = GateIOManager(instrument, conn)
    exchangeManager.initialize()
    loop.create_task(exchangeManager.run())
    loop.create_task(conn.run())

    asyncio.sleep(20)
    #marketOrder = SpotMarketOrder(id="t-qmarket_1", instrument=instrument,
    #                              side=orderSide, amount = amount, price = exchangeManager.localOrderBook.ob.bids[0].price)
    #exchangeManager.sendMarketOrder(marketOrder)

    limitOrder1 = SpotLimitOrder(id="t-qas_0", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price, strategy=DefensiveStrategy())
    limitOrder2 = SpotLimitOrder(id="t-qas_1", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price1, strategy=DefensiveStrategy())

    orders: List[SpotLimitOrder] = list()
    orders.append(limitOrder1)
    orders.append(limitOrder2)

    exchangeManager.sendAllLimitOrders(orders)

    # exchangeManager.sendLimitOrder(limitOrder)
    # limitOrder.price = price = Decimal(0.0035)
    # exchangeManager.amendLimitOrder(limitOrder)
    exchangeManager.cancelAllLimitOrders(orders)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()
