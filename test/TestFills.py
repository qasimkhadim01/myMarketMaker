import asyncio
import logging
from decimal import Decimal
from Test.SimulatedExchange import SimulatedExchange
from connectivity.gateio import Api
from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio.ws import Connection, Configuration, WebSocketResponse
from connectivity.gateio.ws.Spot import SpotUserTradesChannel
from core.Instrument import Instruments
from core.MyEnums import OrderSide, Role
from core.Orders import SpotMarketOrder, FilledOrder, SpotLimitOrder

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s: %(message)s")
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
                                                   OrderSide(result.get('side')), result.get('amount'), result.get('price'), Role(result.get("role")))
            filledOrders.append(filledOrder)
    if 'event' in response:
        logger.debug("received update: %s", result)


async def run():
    while True:
        await asyncio.sleep(10)
        # marketOrder = SpotMarketOrder(id="t-qmarket_1", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price)
        # exchangeManager.sendMarketOrder(marketOrder)
        limitOrder = SpotLimitOrder(id="t-qlimit_1", instrument=instrument, side=OrderSide.Sell, amount=amount,
                                    price=price)
        exchangeManager.sendLimitOrder(limitOrder)


        await asyncio.sleep(1000)
        break


if __name__ == "__main__":
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    sInstrument = "UMEE_USDT"
    instrument = Instruments.instruments.get(sInstrument)
    amount = Decimal(1000)
    price = Decimal(0.004)

    exchangeManager = GateIOManager(sInstrument, conn)

    channel = SpotUserTradesChannel(conn, myCallback)
    channel.subscribe([sInstrument])


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
