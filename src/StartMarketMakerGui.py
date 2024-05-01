import asyncio
import logging
import Static
from decimal import Decimal

from connectivity.ExchangeManagerBase import ExchangeManagerBase
from core.MyEnums import OrderSide
from core.Orders import FilledOrder
from marketmaker.KillSwitch import KillSwitch
from marketmaker.MarketMakerGui import MarketMakerGui
from connectivity.LocalOrderBookBase import LocalOrderBookBase, OrderBookEntry, OrderBook
from connectivity.gateio import Api
from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Coin, Instruments, Instrument
from marketmaker.RiskManager import RiskManager
from marketmaker.Strategy import Strategy, RiskParam
from marketmaker.QuoteManager import QuoteManager

logging.basicConfig(level=logging.ERROR, format=Static.LOGFORMAT,
                    handlers=[logging.FileHandler(Static.logFile, mode='w'),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def dummy(rm: RiskManager, exchangeManager: ExchangeManagerBase):
    await asyncio.sleep(30)
    amount: Decimal = RiskParam.RiskLimit.value
    amount = amount + 100
    midPrice = exchangeManager.localOrderBook.midTob
    RiskManager.risks[Coin.UX].positionValue = amount
    RiskManager.risks[Coin.UX].position = Decimal(amount/midPrice)


if __name__ == '__main__':

    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    instrument = Instruments.instruments.get(str(Instrument(Coin.UX, Coin.USDT)))
    pnlCoin = Coin.USDT
    coins = [instrument.base]

    exchangeManager = GateIOManager(instrument, conn)
    quoteManager = QuoteManager(instrument, exchangeManager)
    localOrderBooks = {}
    [localOrderBooks.update({coin: exchangeManager.localOrderBook}) for coin in coins]
    usdtLocalOrderBook = LocalOrderBookBase(instrument, None)
    bids = []
    bids.append(OrderBookEntry(1, 100000))
    asks = []
    asks.append(OrderBookEntry(1, 100000))
    usdtLocalOrderBook.ob = OrderBook(instrument, "id1", bids, asks)
    localOrderBooks[Coin.USDT] = usdtLocalOrderBook

    rm: RiskManager = RiskManager(coins, pnlCoin, localOrderBooks)

    quoteManager.initialize()
    exchangeManager.initialize()

    loop = asyncio.get_event_loop()
    killSwitch: KillSwitch = KillSwitch(loop)
    loop.create_task(quoteManager.run())
    loop.create_task(exchangeManager.run())
    loop.create_task(exchangeManager.runMyOrderUpdate())
    loop.create_task(conn.run())
    loop.create_task(killSwitch.run())

#    loop.create_task(dummy(rm, exchangeManager))
    marketMakerGui: MarketMakerGui = MarketMakerGui(loop, quoteManager)
    loop.run_forever()
    loop.close()
