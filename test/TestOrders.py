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
    amount = Decimal(2000)
    price = Decimal(0.002400)
    orderSide = OrderSide.Buy

    # exchangeManager = SimulatedExchange(instrument, conn)
    exchangeManager = GateIOManager(instrument, conn)
    #exchangeManager.initialize()

    #marketOrder = SpotMarketOrder(id="t-qmarket_1", instrument=instrument,
    #                              side=orderSide, amount = amount, price = exchangeManager.localOrderBook.ob.bids[0].price)
    #exchangeManager.sendMarketOrder(marketOrder)

    limitOrder1 = SpotLimitOrder(id="t-UMEEQ_40", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price, strategy=DefensiveStrategy())
    #limitOrder2 = SpotLimitOrder(id="t-qas_1", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price, strategy=DefensiveStrategy())
    #limitOrder3 = SpotLimitOrder(id="t-qas_2", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price, strategy=DefensiveStrategy())
    #limitOrder4 = SpotLimitOrder(id="t-qas_3", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price, strategy=DefensiveStrategy())
    #limitOrder5 = SpotLimitOrder(id="t-qas_4", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price, strategy=DefensiveStrategy())
    #limitOrder6 = SpotLimitOrder(id="t-qas_5", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price, strategy=DefensiveStrategy())


    orders: List[SpotLimitOrder] = list()
    orders.append(limitOrder1)

    #exchangeManager.cancelLimitOrder(limitOrder1)
    #exchangeManager.sendLimitOrder(limitOrder1)
    #limitOrder1.price = Decimal(0.002300)
   # exchangeManager.cancelLimitOrder(limitOrder1)

    #exchangeManager.sendMarketOrder(marketOrder)

    #exchangeManager.sendLimitOrder(limitOrder)
    # limitOrder.price = price = Decimal(0.0035)
    #exchangeManager.amendLimitOrder(limitOrder)
    #exchangeManager.cancelAllLimitOrders(orders)
    #exchangeManager.cancelLimitOrder(limitOrder)
    success = exchangeManager.amendAllLimitOrders(orders)
    #exchangeManager.amendLimitOrder(orders[0])
    #exchangeManager.cancelLimitOrder(limitOrder1)


