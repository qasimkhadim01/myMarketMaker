import logging

from connectivity.gateio.ws.Client import BaseChannel

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

class SpotTickerChannel(BaseChannel):
    name = 'spot.tickers'


class SpotPublicTradeChannel(BaseChannel):
    name = 'spot.trades'


class SpotCandlesticksChannel(BaseChannel):
    name = 'spot.candlesticks'


class SpotBookTickerChannel(BaseChannel):
    name = 'spot.book_ticker'


class SpotOrderBookUpdateChannel(BaseChannel):
    name = 'spot.order_book_update'

class SpotOrderPlaceChannel(BaseChannel):
    name = 'spot.order_place'
    require_auth = True
class SpotOrderBookChannel(BaseChannel):
    name = 'spot.order_book'


class SpotOrderChannel(BaseChannel):
    name = 'spot.orders'
    require_auth = True


class SpotUserTradesChannel(BaseChannel):
    name = 'spot.usertrades'
    require_auth = True


class SpotBalanceChannel(BaseChannel):
    name = 'spot.balances'
    require_auth = True


class SpotMarginBalanceChannel(BaseChannel):
    name = 'spot.margin_balances'
    require_auth = True


class SpotFundingBalanceChannel(BaseChannel):
    name = 'spot.funding_balances'
    require_auth = True


class SpotCrossMarginBalanceChannel(BaseChannel):
    name = 'spot.cross_balances'
    require_auth = True