import json
import time
import websockets
import requests
import asyncio
import hmac, hashlib
import logging
from websocket import create_connection

from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, WebSocketResponse, Configuration
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from core.Instrument import Instrument
from core.MyEnums import OrderStatus, OrderSide
from core.Orders import SpotLimitOrder, SpotMarketOrder

logger = logging.getLogger(__name__)


class XXXGateIOManager(ExchangeManagerBase):
    def __init__(self, inInstrument: Instrument, inConn):
        super().__init__(inInstrument, inConn)

    def genSign(self, channel, event, timestamp):
        s = 'channel=%s&event=%s&time=%d' % (channel, event, timestamp)
        sign = hmac.new(Api.SECRET_KEY.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return {'method': 'api_key', 'KEY': Api.API_KEY, 'SIGN': sign}


    def getApiSignature(self, channel, event, timestamp):
        s = 'channel=%s&event=%s&time=%d' % (channel, event, timestamp)
        sign = hmac.new(Api.SECRET_KEY.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return sign

    def login(self):
        ws = create_connection("wss://api.gateio.ws/ws/v4/")

        theTime  = int(time.time())
        request = {
            "time": theTime,
            "channel": "spot.login",
            "event": "api",
            "payload": {
                "api_key": Api.API_KEY,
                "signature": self.getApiSignature("spot.login", "api", theTime),
                "timestamp": "{0}".format(theTime),
                "req_id": "request-1"
            }
        }
        #"signature": self.genSign("spot.login", "api", theTime),
        request['auth'] = self.genSign(request['channel'], request['event'], request['time'])
        ws.send(json.dumps(request))
        data = ws.recv()
        print (data)

    async def topOfBook(self, instrument):
        data = {
            "time": int(time.time()),
            "channel": "spot.order_book_update",
            "event": "subscribe",
            "payload": ["{0}".format(instrument), "100ms"]
        }
        async with websockets.connect(Api.webSocket) as websocket:
            await websocket.send(json.dumps(data))
            while True:
                response = await websocket.recv()
                print(response)

    async def topOfBook2(self, instrument):
        data = {
            "time": int(time.time()),
            "channel": "spot.order_book_update",
            "event": "subscribe",
            "payload": ["{0}".format(instrument), "100ms"]
        }
        async with websockets.connect(Api.webSocket) as websocket:
            await websocket.send(json.dumps(data))
            while True:
                response = await websocket.recv()
                print(response)

    async def orderBookUpdate(self, instrument):
        data = {
            "time": int(time.time()),
            "channel": "spot.order_book_update",
            "event": "subscribe",
            "payload": ["{0}".format(instrument), "100ms"]
        }
        async with websockets.connect(Api.webSocket) as websocket:
            await websocket.send(json.dumps(data))
            while True:
                response = await websocket.recv()
                print(response)

    async def getOrderBookDepth(self, instrument, depth):
        data = {
            "time": int(time.time()),
            "channel": "spot.order_book",
            "event": "subscribe",
            "payload": ["{0}".format(instrument), "{0}".format(depth), "100ms"]
        }
        async with websockets.connect(Api.webSocket) as websocket:
            await websocket.send(json.dumps(data))
            while True:
                response = await websocket.recv()
                print(response)

    async def run(self):
        while True:
            result = await self.orderBookUpdateQueue.get()
            await self.quotesQueue.put(result)

    async def wsMyOrdersCallBack(self, conn: Connection, response: WebSocketResponse):
        if response.error:
            # stop the client if error happened
            conn.close()
            raise response.error
        # ignore subscribe success response
        if 's' not in response.result:
            return
        result = response.result
        logger.debug("received update: %s", result)
        await self.myOrdersUpdateQueue.put(result)

    def sendLimitOrderRest(self, order: SpotLimitOrder):
        host = "https://api.gateio.ws"
        prefix = "/api/v4"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        url = '/spot/orders'
        query_param = ''
        body = {"text": "t-my-custom-id", "currency_pair": "{0}".format(order.instrument)
            , "type": "limit", "account": "spot"
            , "side": "{0}".format(order.side)
            , "amount": "{0}".format(order.amount), "price": "{0}".format(order.price), "stp_act": "cn"}

        #body = '{"text":"t-abc123","currency_pair":"BTC_USDT","type":"limit","account":"unified","side":"buy","amount":"0.001","price":"65000","time_in_force":"gtc","iceberg":"0"}'
        sign_headers = self.genSign('POST', prefix + url, query_param, body)
        headers.update(sign_headers)
        r = requests.request('POST', host + prefix + url, headers=headers, data=body)
        print(r.json())

    def sendLimitOrder(self, order: SpotLimitOrder):
        logger.debug("sendLimitOrder instrument={0}, side={1}"
                     ", price={2}, amount={3}"
                     , order.instrument, order.side, order.price, order.amount)
        # self.spotOrderPlaceChannel.subscribe([order.instrument, order.side, order.price, order.amount])

        placeParam = {"text": "t-my-custom-id", "currency_pair": "{0}".format(order.instrument)
            , "type": "limit", "account": "spot"
            , "side": "{0}".format(order.side)
            , "amount": "{0}".format(order.amount), "price": "{0}".format(order.price), "stp_act": "cn"}

        ws = create_connection("wss://api.gateio.ws/ws/v4/")
        channel = "spot.order_place"

        request = {
            "time": int(time.time()),
            "channel": channel,
            "event": "api",
            "payload": {
                "req_id": "{0}".format(self.nextRequestId),
                "req_param": placeParam
            }
        }
        request['auth'
        ] = self.genSign(request['channel'], request['event'], request['time'])
        ws.send(json.dumps(request))

        for i in range(2):
            data = ws.recv()
            print("data: ", data)

        order.status = OrderStatus.Active

    def sendMarketOrder(self, order: SpotMarketOrder):
        logger.debug(f"sendLimitOrder : {order}")

        modifiedAmount = order.amount if order.side == OrderSide.Sell else order.amount/order.price
        placeParam = {"text": "t-{0}".format(order.id), "currency_pair": "{0}".format(order.instrument)
            ,"type": "market", "account": "spot"
            ,"side": "{0}".format(order.side.value), "amount": "{0}".format(modifiedAmount), "stp_act": "cn"}

        channel = "spot.order_place"
        request = {
            "time": int(time.time()),
            "channel": channel,
            "event": "api",
            "payload": {
                "req_id": "{0}".format(self.nextRequestId),
                "req_param": placeParam
            }
        }

        ws = create_connection(Api.webSocket)

        request['auth'] = self.genSign(request['channel'], request['event'], request['time'])
        ws.send(json.dumps(request))

        response = ws.recv()
        if response.error:
            # stop the client if error happened
            conn.close()
            raise response.error
        # ignore subscribe success response
        if response.data.get("errs") is None:
            raise response.error
        response = ws.recv()
        if "text" in response.result and response.result.get("text") == order.id:
            order.status = OrderStatus.Active
        else:
            raise response.error


    def cancelOrder(self):
        cancelParam = {"order_id": "1694883366", "currency_pair": "GT_USDT"}
        channel = "spot.order_cancel"

        ws = create_connection("wss://api.gateio.ws/ws/v4/")

        ws.send(json.dumps({
            "time": int(time.time()),
            "channel": channel,
            "event": "api",
            "payload": {
                "req_id": "test_1",
                "req_param": cancelParam
            }
        }))
        response = ws.recv()
        print(response)

    def cancelOrderWithParms(self):
        cancelWithIdsParam = [{"id": "1694883366", "currency_pair": "GT_USDT"}]
        channel = "spot.order_cancel_ids"

        ws = create_connection("wss://api.gateio.ws/ws/v4/")

        ws.send(json.dumps({
            "time": int(time.time()),
            "channel": channel,
            "event": "api",
            "payload": {
                "req_id": "test_1",
                "req_param": cancelWithIdsParam
            }
        }))

        print(ws.recv())

    def amendLimitOrder(self, order: SpotLimitOrder):
        amendParam = {"order_id": "{0}}".format(order.id),
                      "currency_pair": "{0}".format(order.instrument)
            , "price": "{0}".format(order.price)}
        channel = "spot.order_amend"

        ws = create_connection("wss://api.gateio.ws/ws/v4/")

        ws.send(json.dumps({
            "time": int(time.time()),
            "channel": channel,
            "event": "api",
            "payload": {
                "req_id": "test_1",
                "req_param": amendParam
            }
        }))

        response = ws.recv()
        print(response)
        order.status = OrderStatus.Active

    def orderStatus(self):
        statusParam = {"order_id": "1694883366", "currency_pair": "GT_USDT"}
        channel = "spot.order_status"

        ws = create_connection("wss://api.gateio.ws/ws/v4/")

        ws.send(json.dumps({
            "time": int(time.time()),
            "channel": channel,
            "event": "api",
            "payload": {
                "req_id": "test_1",
                "req_param": statusParam
            }
        }))

        print(ws.recv())


if __name__ == '__main__':
    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    instrument = "BTC_USDT"
    loop = asyncio.get_event_loop()
    exchangeManager = GateIOManager(instrument, conn)
    exchangeManager.initialize()
    loop.create_task(exchangeManager.run())
    loop.create_task(conn.run())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()
