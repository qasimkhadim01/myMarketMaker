import asyncio
import itertools
import logging
import sys
import typing
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from connectivity.gateio.ws.Client import Configuration, Connection, WebSocketResponse
from connectivity.gateio.ws.Spot import SpotOrderBookUpdateChannel
from connectivity.gateio.ws.Spot import SpotOrderBookChannel

logger = logging.getLogger(__name__)

class Base:
    def callback(self, conn: Connection, response: WebSocketResponse):
        print('Callback Base Recieved')

class Test(Base):
    def callback(self, conn: Connection, response: WebSocketResponse):
        super().callback(conn, response)
        print('Callback child Recieved')
        result = response.result
        logger.debug("received update: %s", result)


logging.basicConfig(level=logging.ERROR, format="%(asctime)s: %(message)s")
conn = Connection(Configuration())
demo_cp = 'UMEE_USDT'
channel = SpotOrderBookChannel(conn, Test().callback)
channel.subscribe([demo_cp, "5", "100ms"])

loop = asyncio.get_event_loop()

#loop.create_task(order_book.run())
loop.create_task(conn.run())

try:
    loop.run_forever()
except KeyboardInterrupt:
    for task in asyncio.Task.all_tasks(loop):
        task.cancel()
    loop.close()