import logging
from decimal import Decimal
from typing import List

import Static
from Test import Api
from connectivity.gateio import Utils
from core.Instrument import Instrument, Instruments, Coin
from core.MyEnums import OrderSide
from core.Orders import Order, SpotLimitOrder
import requests

logging.basicConfig(level=logging.ERROR, format=Static.LOGFORMAT,
                    handlers=[logging.FileHandler(Static.logFile, mode='w'),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

            orders.append(order)
        if orders is not None:
            [logger.error(order) for order in orders]
            logger.error(f"Total count {len(orders)}")

    except:
        logging.exception('')

    def cancelAllOpenOrders(instrument: Instrument):
        url = '/spot/orders'
        query_param = f"currency_pair={str(instrument)}"
        sign_headers = Utils.genSignRest('DELETE', Api.prefix + url, query_param)
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


if __name__ == '__main__':
    logger.debug("Orders before cancelling....")
    orderList()
    #cancelOpenOrders(Instruments.instruments.get(str(Instrument(Coin.UX, Coin.USDT))))
    #logger.debug("Orders after cancelling....")
    #marketTrades()