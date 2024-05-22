import logging
from typing import List

import Static
from connectivity.gateio import Api
from connectivity.gateio.GateIOManager import GateIOManager
from core.Instrument import Instrument, Instruments, Coin
from core.Orders import Order
import requests

logging.basicConfig(level=logging.ERROR, format=Static.LOGFORMAT,
                    handlers=[logging.FileHandler(Static.logFile, mode='w'),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def cancelOpenOrders(instrument: Instrument):
    GateIOManager.cancelAllOpenOrders(instrument)
def orderList():
    orders: List[Order] = GateIOManager.listAllOrders()
    if orders is not None :
        [logger.error(order) for order in orders]
        logger.error(f"Total count {len(orders)}")

def marketTrades():

    url = '/spot/my_trades'
    query_param = ''
    # for `gen_sign` implementation, refer to section `Authentication` above
    sign_headers = GateIOManager.genSignRest('GET', Api.prefix + url, query_param)
    Api.restHeaders.update(sign_headers)
    r = requests.request('GET', Api.restHost + Api.prefix + url, headers=Api.restHeaders)
    print(r.json())

if __name__ == '__main__':
    logger.debug("Orders before cancelling....")
    orderList()
    #cancelOpenOrders(Instruments.instruments.get(str(Instrument(Coin.UX, Coin.USDT))))
    #logger.debug("Orders after cancelling....")
    #marketTrades()