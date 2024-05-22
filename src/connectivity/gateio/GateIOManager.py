import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import List, Dict

import requests
import websockets
from websocket import create_connection

import Static
from connectivity.ExchangeManagerBase import ExchangeManagerBase
from connectivity.LocalOrderBookBase import OrderBookEntry
from connectivity.gateio import Api, Utils
from connectivity.gateio.LocalOrderBook import LocalOrderBook
from connectivity.gateio.ws import Connection, WebSocketResponse, Configuration
from connectivity.gateio.ws.Client import BaseChannel
from connectivity.gateio.ws.Spot import SpotUserTradesChannel, SpotBookTickerChannel
from core.Instrument import Instrument, Instruments
from core.MyEnums import OrderStatus, OrderSide, Role
from core.Orders import SpotLimitOrder, SpotMarketOrder, FilledOrder

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
Static.appLoggers.append(logger)


class GateIOManager(ExchangeManagerBase):
    def __init__(self, instruments: List[Instrument], conn: Connection):
        super().__init__(instruments, conn)
        self.localOrderBooks:Dict[Instrument, LocalOrderBook] = dict()
        [self.localOrderBooks.update({instrument:LocalOrderBook(instrument, self.conn, self.localOrderBookUpdateQueue[instrument])}) for instrument in instruments]
        self.conn = conn

    def split(self, orders, maxSize):
        for i in range(0, len(orders), maxSize):
            yield orders[i:i + maxSize]


    def initialize(self):
        [localOrderBook.initialize() for localOrderBook in self.localOrderBooks.values()]
        self.userTradeChannel = SpotUserTradesChannel(self.conn, self.wsMyTradesCallBack)
        self.bookTickerChannel = SpotBookTickerChannel(self.conn, self.wsTopOfBookCallBack)
        self.bookTickerChannel.subscribe([str(instrument) for instrument in self.instruments])
        self.userTradeChannel.subscribe([str(instrument) for instrument in self.instruments] + [str(Static.KillInstrument)])


    def release(self):
        self.bookTickerChannel.unsubscribe([str(instrument) for instrument in self.instruments])
        self.userTradeChannel.unsubscribe([str(instrument) for instrument in self.instruments] + [str(Static.KillInstrument)])
        self.conn.unregister(self.userTradeChannel)
        self.conn.unregister(self.bookTickerChannel)
        self.conn.close()

    @staticmethod
    def genSignWs(channel, event, timestamp):
        s = 'channel=%s&event=%s&time=%d' % (channel, event, timestamp)
        sign = hmac.new(Api.SECRET_KEY.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return {'method': 'api_key', 'KEY': Api.API_KEY, 'SIGN': sign}
    @staticmethod
    def genSignRest(method, url, query_string=None, payload_string=None):
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
        request['auth'] = GateIOManager.genSignRest(request['channel'], request['event'], request['time'])
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
        instrument = Instruments.instruments[result['s']]
        self.localOrderBooks[instrument].topOfBookBid = OrderBookEntry(round(Decimal(result['b']), instrument.pricePrecision), round(Decimal(result['B']), instrument.amountPrecision))
        self.localOrderBooks[instrument].topOfBookAsk = OrderBookEntry(round(Decimal(result['a']), instrument.pricePrecision), round(Decimal(result['A']), instrument.amountPrecision))
        self.localOrderBooks[instrument].tobTimeStamp = datetime.now()
        await self.localOrderBookUpdateQueue[instrument].put(result)

    async def wsMyTradesCallBack(self, conn: Connection, response: WebSocketResponse):
        try:
            logger.debug("received message")
            if response.error:
                logger.error(f"Error {response.error}")
                # stop the client if error happened
                conn.close()
                raise response.error
            # ignore subscribe success response
            result = response.result
            logger.debug(f"received {result}")
            if response.event == 'update' and response.channel == "spot.usertrades":
                logger.debug("received update event")
                results = response.result

                filledOrders: List[FilledOrder] = list()

                for result in results:
                    filledInstrument = Instruments.instruments.get(result.get('currency_pair'))
                    if filledInstrument == Static.KillInstrument:
                        Static.Kill = True
                        return
                    if filledInstrument in self.instruments:
                        filledOrder: FilledOrder = FilledOrder(result.get('text'), filledInstrument,
                                                               OrderSide(result.get('side')),
                                                               Decimal(result.get('amount')),
                                                               result.get('price'), Role(result.get("role")))
                        filledOrders.append(filledOrder)
                    else:
                        logger.error(f"Unexpected instrument {str(filledInstrument)}")
                if len(filledOrders) > 0: await self.myOrdersUpdateQueue.put(filledOrders)
        except:
            logger.exception('')

    def sendAllLimitOrders3(self, orders: List[SpotLimitOrder]):
        for order in orders:
            self.sendLimitOrder(order)

    def sendLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"sendLimitOrder enter : {order}")
        query_param = ''
        url = '/spot/orders'
        body = {"text": format(order.id), "currency_pair": "{0}".format(str(order.instrument)), "type": "limit",
                "account": "spot", "side": "{0}".format(order.side.value), "amount": "{0}".format(order.amount),
                "price": "{0:.6f}".format(order.price), "time_in_force": "gtc", "iceberg": "0"}

        requestContent = json.dumps(body)
        sign_headers = GateIOManager.genSignRest('POST', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)

        try:
            response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                result = response.json()
                if "text" in result and result.get("text") == order.id:
                    order.status = OrderStatus.Active
        except requests.exceptions.RequestException as e:
            logger.error("failed to create quote: %s", order)

    def sendMarketOrder(self, order: SpotMarketOrder):
        logger.error(f"sendMarketOrder {order}")
        modifiedAmount = order.amount if order.side == OrderSide.Sell else order.amount * order.price

        url = '/spot/orders'
        query_param = ''
        body = {"text": format(order.id), "currency_pair": "{0}".format(str(order.instrument)), "type": "market",
                "account": "spot", "side": "{0}".format(order.side.value),
                "amount": "{0}".format(modifiedAmount), "time_in_force": "fok"}

        requestContent = json.dumps(body)
        sign_headers = self.genSignRest('POST', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)

        response = None
        try:
            response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                result = response.json()
                if "text" in result and result.get("text") == order.id:
                    order.status = OrderStatus.Active
                logger.debug(f"completed  : {order}")
                return True
            else:
                logger.error(f"Response not ok for market order {order}")

        except requests.exceptions.RequestException as e:
            logging.exception(response.text)
            return False
    def sendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        logger.debug(f"Enter")
        var = [logger.debug(f"{order}") for order in orders]

        url = '/spot/batch_orders'
        query_param = ''

        chunks = list(self.split(orders, 5))

        for chunk in chunks:
            logger.debug("Processing chunk")
            body = []
            for order in chunk:
                bodyItem = {"text": format(order.id), "currency_pair": "{0}".format(str(order.instrument)), "type": "limit",
                        "account": "spot", "side": "{0}".format(order.side.value), "amount": "{0}".format(order.amount),
                        "price": "{0:.6f}".format(order.price), "time_in_force": "gtc", "iceberg": "0"}
                body.append(bodyItem)

            requestContent = json.dumps(body)
            sign_headers = GateIOManager.genSignRest('POST', Api.prefix + url, query_param, requestContent)
            Api.restHeaders.update(sign_headers)

            response = None
            try:
                response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                            data=requestContent)
                response.raise_for_status()
                if response.ok:
                    for order in orders:
                        order.status = OrderStatus.Active
                logger.error("Successfully send all limit orders")

            except requests.exceptions.RequestException as e:
                logging.exception(response.text)
                logger.error("failed to send all orders in chunk: %s")

    def cancelLimitOrder(self, order: SpotLimitOrder):
        logger.debug(f"cancelLimitOrder enter : {order}")
        url = '/spot/cancel_batch_orders'
        query_param = ''
        body = {"currency_pair": "{0}".format(str(order.instrument)), "id": format(order.id)}
        requestContent = json.dumps(body)

        sign_headers = GateIOManager.genSignRest('POST', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)
        response = None
        try:
            response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                order.status = OrderStatus.Cancelled
        except requests.exceptions.RequestException as e:
            logging.exception('')
            logger.error("failed to cancel order: %s", order)
        finally:
            logger.debug("exit")

    def cancelAllLimitOrders2(self, orders: List[SpotLimitOrder]):
        for order in orders:
            self.cancelLimitOrder(order)

    def cancelAllLimitOrders(self, orders: List[SpotLimitOrder]):
        if len(orders) == 0: return
        logger.info(f" Cancelling all limit orders")
        var = [logger.info(f"{order.id}") for order in orders]
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
            logger.debug("successfully cancelled all orders")

        except requests.exceptions.RequestException as e:
            logging.exception('')
            logger.error("failed to cancel all orders: %s")
        finally:
            logger.debug("exit")

    @staticmethod
    def cancelAllOpenOrders(instrument: Instrument):
        url = '/spot/orders'
        query_param = f"currency_pair={str(instrument)}"
        sign_headers = GateIOManager.genSignRest('DELETE', Api.prefix + url, query_param)
        Api.restHeaders.update(sign_headers)

        try:
            response = requests.request('DELETE', Api.restHost + Api.prefix + url + "?" + query_param,
                                        headers=Api.restHeaders)
            response.raise_for_status()
            if response.ok:
                logger.info("successfully cancelled all orders")

        except requests.exceptions.RequestException as e:
            logging.exception('')
            logger.error("failed to cancel all orders: %s")

    @staticmethod
    def cancelAll():
        url = '/spot/price_orders'
        query_param = ''
        # for `gen_sign` implementation, refer to section `Authentication` above
        sign_headers = GateIOManager.genSignRest('DELETE', Api.prefix + url, query_param)
        Api.restHeaders.update(sign_headers)
        r = requests.request('DELETE', Api.restHost + Api.prefix + url, headers=Api.restHeaders)
        print(r.json())

    @staticmethod
    def listAllOrders():
        url = '/spot/open_orders'
        query_param = ''
        # for `gen_sign` implementation, refer to section `Authentication` above
        sign_headers = Utils.genSignRest('GET', Api.prefix + url, query_param)
        Api.restHeaders.update(sign_headers)
        response = requests.request('GET', Api.restHost + Api.prefix + url, headers=Api.restHeaders)
        orders: List[SpotLimitOrder] = list()
        try:
            for item in response.json()[0]["orders"]:
                order: SpotLimitOrder = SpotLimitOrder(item["text"], Instruments.instruments.get(item["currency_pair"]),
                                                       OrderSide(item["side"])
                                                       , Decimal(item["amount"]), Decimal(item["price"]), None)

                order.updateTime = int(item["update_time"])
                orders.append(order)
            return orders
        except:
            logging.exception('')

    def amendAllLimitOrders2(self, orders: List[SpotLimitOrder]):
        for order in orders:
            self.amendLimitOrder(order)

    def amendAllLimitOrders(self, orders: List[SpotLimitOrder]):
        if len(orders) == 0: return
        logger.debug("enter")
        failedOrders: List[SpotLimitOrder] = list()
        url = '/spot/amend_batch_orders'
        query_param = ''

        chunks = list(self.split(orders, 5))

        for chunk in chunks:
            logger.debug("Processing chunk")
            body = []
            for order in chunk:
                logger.info(f"{order}")

                bodyItem = {"currency_pair": "{0}".format(str(order.instrument)), "order_id": format(order.id),
                            "price": "{0:.6f}".format(order.price), "account": "spot", "amend_text": "test"}
                body.append(bodyItem)

            requestContent = json.dumps(body)

            sign_headers = GateIOManager.genSignRest('POST', Api.prefix + url, query_param, requestContent)
            Api.restHeaders.update(sign_headers)

            response = None

            try:
                response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                            data=requestContent)
                response.raise_for_status()
                if response.ok:
                    results = response.json()
                    for i in range(len(results)):
                        if (not results[i]["succeeded"]
                                and (results[i]["label"] == "INVALID_PARAM_VALUE" or results[i]["label"] == "ORDER_NOT_FOUND")):
                            logger.error (f"Amend orders failed {results[i]['label']} {results[i]['message']}")
                            failedOrders.append(orders[i])
                    for order in chunk:
                        order.status = OrderStatus.Active
                logger.debug("exit")
            except requests.exceptions.RequestException as e:
                logging.exception('')
                logger.error("failed to amend all orders: %s")
        return failedOrders

    def amendAllLimitOrdersXX(self, orders: List[SpotLimitOrder]):
        if len(orders) == 0: return

        failedOrders: List[SpotLimitOrder] = list()
        var = [logger.info(f"{order}") for order in orders]
        url = '/spot/amend_batch_orders'
        query_param = ''

        body = []
        for order in orders:
            bodyItem = {"currency_pair": "{0}".format(str(order.instrument)), "order_id": format(order.id),
                        "price": "{0:.6f}".format(order.price), "account": "spot", "amend_text": "test"}
            body.append(bodyItem)

        requestContent = json.dumps(body)

        sign_headers = GateIOManager.genSignRest('POST', Api.prefix + url, query_param, requestContent)
        Api.restHeaders.update(sign_headers)

        response = None

        try:
            response = requests.request('POST', Api.restHost + Api.prefix + url, headers=Api.restHeaders,
                                        data=requestContent)
            response.raise_for_status()
            if response.ok:
                results =response.json()
                for i in range(len(results)):
                    if not results[i]["succeeded"] and results[i]["label"] == "ORDER_NOT_FOUND":
                        failedOrders.append(orders[i])
                for order in orders:
                    order.status = OrderStatus.Active
            logger.info("successfully amended all orders")
        except requests.exceptions.RequestException as e:
            logging.exception('')
            logger.error("failed to amend all orders: %s")
        finally:
            return failedOrders

    def amendLimitOrder(self, order: SpotLimitOrder):
        logger.info(f"amend limitOrder enter  : {order}")
        url = '/spot/orders/{0}'.format(order.id)
        query_param = 'currency_pair={0}'.format(str(order.instrument))
        body = {"currency_pair": "{0}".format(str(order.instrument)), "id": format(order.id),
                "price": "{0:.6f}".format(order.price)}

        requestContent = json.dumps(body)

        sign_headers = GateIOManager.genSignRest('PATCH', Api.prefix + url, query_param, requestContent)
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
            logging.exception('')
            logger.error(f"Could not amend quote, probably because filled. {order}")

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

    instruments:List[Instrument] = list()
    instruments.append(Instruments.instruments["ETH_USDT"])
    instruments.append(Instruments.instruments["BTC_USDT"])


    loop = asyncio.get_event_loop()
    exchangeManager = GateIOManager(instruments, conn)
    exchangeManager.initialize()
    loop.create_task(exchangeManager.run())
    loop.create_task(conn.run())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks(loop):
            task.cancel()
        loop.close()
