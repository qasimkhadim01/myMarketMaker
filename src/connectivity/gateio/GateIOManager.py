import json
import time
from typing import List

import websockets
import requests
import asyncio
import hmac, hashlib
import logging
from websocket import create_connection
from decimal import Decimal
import Static
from connectivity.gateio import Api
from connectivity.gateio.LocalOrderBook import LocalOrderBook
from connectivity.gateio.ws import Connection, WebSocketResponse, Configuration
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from connectivity.gateio.ws.Spot import SpotUserTradesChannel, SpotBookTickerChannel
from core.Instrument import Instrument, Instruments
from core.MyEnums import OrderStatus, OrderSide, Role
from core.Orders import SpotLimitOrder, SpotMarketOrder, FilledOrder

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GateIOManager(ExchangeManagerBase):
    def __init__(self, inInstrument: Instrument, inConn: Connection):
        super().__init__(inInstrument, inConn)
        self.localOrderBook = LocalOrderBook(self.instrument, self.conn, self.orderBookUpdateQueue)
        self.conn = inConn

    def initialize(self):
        self.localOrderBook.initialize()  # only start receiving call backs once all other essentials init
        self.userTradeChannel = SpotUserTradesChannel(self.conn, self.wsMyTradesCallBack)
        self.userTradeChannel.subscribe([str(self.instrument), str(Static.KillInstrument)])

        self.bookTickerChannel = SpotBookTickerChannel(self.conn, self.wsTopOfBookCallBack)
        self.bookTickerChannel.subscribe([str(self.instrument)])

    def release(self):
        self.userTradeChannel.unsubscribe([str(self.instrument)])
        self.bookTickerChannel.unsubscribe([str(self.instrument)])
        self.conn.unregister(self.userTradeChannel)
        self.conn.unregister(self.bookTickerChannel)
        self.conn.close()

    def genSignWs(self, channel, event, timestamp):
        s = 'channel=%s&event=%s&time=%d' % (channel, event, timestamp)
        sign = hmac.new(Api.SECRET_KEY.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return {'method': 'api_key', 'KEY': Api.API_KEY, 'SIGN': sign}

    def genSignRest(self, method, url, query_string=None, payload_string=None):
        t = time.time()
        m = hashlib.sha512()
        m.update((payload_string or "").encode('utf-8'))
        hashed_payload = m.hexdigest()
        s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
        sign = hmac.new(Api.SECRET_KEY.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return {'KEY': Api.API_KEY, 'Timestamp': str(t), 'SIGN': sign}

    def getApiSignature(self, channel, event, timestamp):
        s = 'channel=%s&event=%s&time=%d' % (channel, event, timestamp)
        sign = hmac.new(Api.SECRET_KEY.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return sign

    def login(self):
        ws = create_connection("wss://api.gateio.ws/ws/v4/")

        theTime = int(time.time())
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
        # "signature": self.genSign("spot.login", "api", theTime),
        request['auth'] = self.genSign(request['channel'], request['event'], request['time'])
        ws.send(json.dumps(request))
        data = ws.recv()
        logger.debug(f"data received {data}")

    async def topOfBook(self, instrument: Instrument):
        data = {
            "time": int(time.time()),
            "channel": "spot.order_book_update",
            "event": "subscribe",
            "payload": ["{0}".format(str(instrument)), "100ms"]
        }
        async with websockets.connect(Api.webSocket) as websocket:
            await websocket.send(json.dumps(data))
            while True:
                response = await websocket.recv()
                print(response)

    async def topOfBook2(self, instrument: Instrument):
        data = {
            "time": int(time.time()),
            "channel": "spot.order_book_update",
            "event": "subscribe",
            "payload": ["{0}".format(str(instrument)), "100ms"]
        }
        async with websockets.connect(Api.webSocket) as websocket:
            await websocket.send(json.dumps(data))
            while True:
                response = await websocket.recv()
                print(response)

    async def orderBookUpdate(self, instrument: Instrument):
        data = {
            "time": int(time.time()),
            "channel": "spot.order_book_update",
            "event": "subscribe",
            "payload": ["{0}".format(str(instrument)), "100ms"]
        }
        async with websockets.connect(Api.webSocket) as websocket:
            await websocket.send(json.dumps(data))
            while True:
                response = await websocket.recv()
                print(response)

    async def getOrderBookDepth(self, instrument: Instrument, depth):
        data = {
            "time": int(time.time()),
            "channel": "spot.order_book",
            "event": "subscribe",
            "payload": ["{0}".format(str(instrument)), "{0}".format(depth), "100ms"]
        }
        async with websockets.connect(Api.webSocket) as websocket:
            await websocket.send(json.dumps(data))
            while True:
                response = await websocket.recv()
                print(response)

    async def run(self):
        while Static.KeepRunning:
            result = await self.orderBookUpdateQueue.get()
            await self.quotesQueue.put(result)
        logging.error("Kill Switch Triggered")

    async def wsTopOfBookCallBack(self, conn: Connection, response: WebSocketResponse):
        if response.error:
            # stop the client if error happened
            conn.close()
            raise response.error
        # ignore subscribe success response
        if 's' not in response.result:
            return
        result = response.result
        logger.debug("received TOB update: %s", result)
        await self.orderBookUpdateQueue.put(result)

    async def wsMyTradesCallBack(self, conn: Connection, response: WebSocketResponse):
        logger.debug("received message")
        try:
            if response.error:
                # stop the client if error happened
                conn.close()
                raise response.error
            # ignore subscribe success response
            result = response.result
            if response.event == 'update' and response.channel == "spot.usertrades":
                results = response.result

                filledOrders: List[FilledOrder] = list()

                for result in results:
                    filledInstrument = Instruments.instruments.get(result.get('currency_pair'))
                    if filledInstrument == Static.KillInstrument:
                        Static.Kill = True
                        return
                    if filledInstrument == self.instrument:
                        filledOrder: FilledOrder = FilledOrder(result.get('text'), filledInstrument,
                                                               OrderSide(result.get('side')), Decimal(result.get('amount')),
                                                               result.get('price'), Role(result.get("role")))
                        filledOrders.append(filledOrder)
                    else:
                        logger.error(f"expecting instrument {str(instrument)} received {str(filledInstrument)}")
                logger.debug("received myOrdersUpdate: %s", result)
                if len(filledOrders) > 0: await self.myOrdersUpdateQueue.put(filledOrders)
        except:
            logger.exception('')

    def sendLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"sendLimitOrder enter : {order}")
        query_param = ''
        body = {"text": format(order.id), "currency_pair": "{0}".format(str(order.instrument)), "type": "limit",
                "account": "spot", "side": "{0}".format(order.side.value), "amount": "{0}".format(order.amount),
                "price": "{0:.6f}".format(order.price), "time_in_force": "gtc", "iceberg": "0"}

        requestContent = json.dumps(body)
        sign_headers = self.genSignRest('POST', Api.prefix + Api.restUrlOrders, query_param, requestContent)
        Api.restHeaders.update(sign_headers)

        try:
            response = requests.request('POST', Api.restHost + Api.prefix + Api.restUrlOrders, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                result = response.json()
                if "text" in result and result.get("text") == order.id:
                    order.status = OrderStatus.Active
        except requests.exceptions.RequestException as e:
            logger.error("failed to create quote: %s", order)

    def sendMarketOrder(self, order: SpotMarketOrder):
        logger.debug(f"sendMarketOrder enter  : {order}")
        modifiedAmount = order.amount if order.side == OrderSide.Sell else order.amount * order.price

        query_param = ''
        body = {"text": format(order.id), "currency_pair": "{0}".format(str(order.instrument)), "type": "market",
                "account": "spot", "side": "{0}".format(order.side.value),
                "amount": "{0}".format(modifiedAmount), "time_in_force": "fok"}

        requestContent = json.dumps(body)
        sign_headers = self.genSignRest('POST', Api.prefix + Api.restUrlOrders, query_param, requestContent)
        Api.restHeaders.update(sign_headers)

        response = None
        try:
            response = requests.request('POST', Api.restHost + Api.prefix + Api.restUrlOrders, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                result = response.json()
                if "text" in result and result.get("text") == order.id:
                    order.status = OrderStatus.Active
        except requests.exceptions.RequestException as e:
            logging.exception(response.text)

    def sendAllLimitOrders(self, orders:List[SpotLimitOrder]):
        logger.debug(f" sending new limit orders")
        var = [logger.debug(f"{order.id}" for order in orders)]

        url = '/spot/batch_orders'
        query_param = ''


        body = []
        for order in orders:
            bodyItem = {"text": format(order.id), "currency_pair": "{0}".format(str(order.instrument)), "type": "limit",
                    "account": "spot", "side": "{0}".format(order.side.value), "amount": "{0}".format(order.amount),
                    "price": "{0:.6f}".format(order.price), "time_in_force": "gtc", "iceberg": "0"}
            body.append(bodyItem)

        requestContent = json.dumps(body)
        # for `gen_sign` implementation, refer to section `Authentication` above

        sign_headers = self.genSignRest('POST', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)

        response = None
        try:
            response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                for order in orders:
                    order.status = OrderStatus.Active
            logger.info("successfully sent all orders")

        except requests.exceptions.RequestException as e:
            logging.exception(response.text)
            logger.error("failed to send all orders: %s")

    def cancelLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"cancelLimitOrder enter : {order}")
        url = '/spot/cancel_batch_orders'
        query_param = ''
        body = {"currency_pair": "{0}".format(str(order.instrument)), "id": format(order.id)}
        requestContent = json.dumps(body)

        sign_headers = self.genSignRest('POST', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)
        response = None
        try:
            response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                order.status = OrderStatus.Cancelled
        except requests.exceptions.RequestException as e:
            logging.exception(response.text)
            logger.error("failed to cancel order: %s", order)

    def cancelAllLimitOrders(self, orders: List[SpotLimitOrder]):
        for order in orders:
            self.cancelLimitOrder(order)


    def cancelAllLimitOrders2(self, orders: List[SpotLimitOrder]):
        logger.debug(f" Cancelling all limit orders")
        var = [logger.debug(f"{order.id}") for order in orders]
        url = '/spot/cancel_batch_orders'
        query_param = ''

        body = []
        for order in orders:
            bodyItem = {"currency_pair": "{0}".format(str(order.instrument)), "id": format(order.id)}
            body.append(bodyItem)

        requestContent = json.dumps(body)
        # for `gen_sign` implementation, refer to section `Authentication` above

        sign_headers = self.genSignRest('POST', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)

        response = None
        try:
            response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                for order in orders:
                    order.status = OrderStatus.Cancelled
            logger.info("successfully cancelled all orders")

        except requests.exceptions.RequestException as e:
            logging.exception(response.text)
            logger.error("failed to cancel all orders: %s")

    def amendAllLimitOrders2(self, orders: List[SpotLimitOrder]):
        for order in orders:
            self.amendLimitOrder(order)

    def amendAllLimitOrders(self, orders:List[SpotLimitOrder]):
        var = [logger.debug(f"{order.id}") for order in orders]
        url = '/spot/amend_batch_orders'
        query_param = ''
        body = '[{"order_id":"121212","currency_pair":"BTC_USDT","account":"spot","amount":"1","amend_text":"test"}]'

        body = []
        for order in orders:
            bodyItem = {"currency_pair": "{0}".format(str(order.instrument)), "id": format(order.id),
                    "price": "{0:.6f}".format(order.price)}
            body.append(bodyItem)

        requestContent = json.dumps(body)
        # for `gen_sign` implementation, refer to section `Authentication` above

        sign_headers = self.genSignRest('POST', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)

        response = None
        try:
            response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                for order in orders:
                    order.status = OrderStatus.Active
            logger.info("successfully cancelled all orders")

        except requests.exceptions.RequestException as e:
            logging.exception(response.text)
            logger.error("failed to amend all orders: %s")


    def amendLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"amend limitOrder enter  : {order}")
        url = '/spot/orders/{0}'.format(order.id)
        query_param = 'currency_pair={0}'.format(str(order.instrument))
        body = {"currency_pair": "{0}".format(str(order.instrument)), "id": format(order.id),
                "price": "{0:.6f}".format(order.price)}

        requestContent = json.dumps(body)

        sign_headers = self.genSignRest('PATCH', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)
        response = None
        try:
            response = requests.request('PATCH', Api.restHost + Api.prefix + url + "?" + query_param,
                                        headers=Api.restHeaders, data=requestContent)

            response.raise_for_status()
            if response.ok:
                result = response.json()
                if "text" in result and result.get("text") == order.id:
                    order.status = OrderStatus.Active
                    return True
        except requests.exceptions.RequestException as e:
            logging.exception(response.text)
            logger.error("failed to amend quote: %s", order)

        return False

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
    FORMAT = "[%(asctime)s:%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT,
                        handlers=[logging.FileHandler(Static.logFile, mode='w'),
                                  logging.StreamHandler()])
    logger = logging.getLogger()

    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    instrument = Instruments.instruments["UMEE_USDT"]

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
