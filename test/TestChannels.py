import asyncio
import logging
import hmac, hashlib
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, Configuration, WebSocketResponse
from connectivity.gateio.ws.Spot import SpotOrderBookUpdateChannel, SpotUserTradesChannel, SpotOrderPlaceChannel, \
    SpotOrderChannel

logging.basicConfig(level=logging.ERROR, format="%(asctime)s: %(message)s")
logger = logging.getLogger()


async def myCallback(conn: Connection, response: WebSocketResponse):
    if response.error:
        # stop the client if error happened
        conn.close()
        raise response.error
    # ignore subscribe success response
    if 's' not in response.result:
        return
    result = response.result
    logger.debug("received update: %s", result)


def genSignWs(self, channel, event, timestamp):
    s = 'channel=%s&event=%s&time=%d' % (channel, event, timestamp)
    sign = hmac.new(Api.SECRET_KEY.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'method': 'api_key', 'KEY': Api.API_KEY, 'SIGN': sign}


async def run():
    while True:
        print('here')
        await asyncio.sleep(1000)


if __name__ == '__main__':
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    demo_cp = 'BTC_USDT'

    # channel = SpotOrderChannel(conn, myCallback)
    # channel.subscribe([demo_cp, "100ms"])

    channel = SpotUserTradesChannel(conn, myCallback)
    channel.subscribe([demo_cp])

    loop = asyncio.get_event_loop()
    loop.create_task(run())
    loop.create_task(conn.run())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()
