import asyncio
import logging
from decimal import Decimal

import Static
from connectivity.gateio import Api
from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio.ws import Connection, Configuration, WebSocketResponse
from connectivity.gateio.ws.Spot import SpotUserTradesChannel
from core.Instrument import Instruments
from core.MyEnums import OrderSide, Role
from core.Orders import FilledOrder, SpotLimitOrder, SpotMarketOrder

FORMAT = "[%(asctime)s:%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT,
                    handlers=[logging.FileHandler(Static.logFile, mode='w'),
                              logging.StreamHandler()])
logger = logging.getLogger()


async def myCallback(conn: Connection, response: WebSocketResponse):
    if response.error:
        # stop the client if error happened
        conn.close()
        raise response.error
    # ignore subscribe success response
    result = response.result
    if response.event == 'update' and response.channel == "spot.usertrades":
        results = response.result

        filledOrders: [] = []
        for result in results:
            filledOrder: FilledOrder = FilledOrder(result.get('text'), result.get('currency_pair'),
                                                   OrderSide(result.get('side')), Decimal(result.get('amount')), Decimal(result.get('price')), Role(result.get("role")))
            filledOrders.append(filledOrder)

        if isinstance(filledOrders, list):
            filledOrderAggregates: dict[str] = dict()
            for filledOrder in filledOrders:
                if filledOrder.id not in filledOrderAggregates.keys():
                    filledOrderAggregates[filledOrder.id] = FilledOrder(filledOrder.id, filledOrder.instrument
                                            , filledOrder.side, Decimal(0.0)
                                            , filledOrder.price, filledOrder.role)
                filledOrderAggregates[filledOrder.id].filledAmount += filledOrder.filledAmount



    if 'event' in response:
        logger.debug("received update: %s", result)


async def run():
    while True:
        await asyncio.sleep(20)
        marketOrder = SpotMarketOrder(id="t-qmarket_1", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price)
        exchangeManager.sendMarketOrder(marketOrder)
#        limitOrder = SpotLimitOrder(id="t-qlimit_1", instrument=instrument, side=OrderSide.Sell, amount=amount,
 #                                   price=price)
 #       exchangeManager.sendLimitOrder(limitOrder)
        await asyncio.sleep(1000)
        break


if __name__ == "__main__":
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    sInstrument = "UMEE_USDT"
    instrument = Instruments.instruments.get(sInstrument)
    amount = Decimal(60000)
    price = Decimal(0.004)

    channel = SpotUserTradesChannel(conn, myCallback)
    channel.subscribe([sInstrument])

    #the spot user trades channel is already subscribed to in the below
    exchangeManager = GateIOManager(instrument, conn)
    exchangeManager.initialize()


    # limitOrder = SpotLimitOrder(id="t-qlimit_1", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price)
    # exchangeManager.sendLimitOrder(limitOrder)
    # limitOrder.price = price = Decimal(0.0035)
    # exchangeManager.amendLimitOrder(limitOrder)
    # exchangeManager.cancelLimitOrder(limitOrder)

    loop = asyncio.get_event_loop()
    loop.create_task(run())
    loop.create_task(conn.run())


    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()
