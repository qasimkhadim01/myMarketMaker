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
        print(response)

async def run():
    while True:
        print ('sleeping')
        await asyncio.sleep(20)



if __name__ == "__main__":
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    sInstrument = "XRP_USDT"
    instrument = Instruments.instruments.get(sInstrument)
    channel = SpotUserTradesChannel(conn, myCallback)
    channel.subscribe([sInstrument])

    loop = asyncio.get_event_loop()
    loop.create_task(run())
    loop.create_task(conn.run())


    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()
