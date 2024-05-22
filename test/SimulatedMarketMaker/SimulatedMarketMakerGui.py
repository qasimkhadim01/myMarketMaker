import asyncio
import logging
from typing import List

from sortedcontainers import SortedList

import Static
from decimal import Decimal

from Test.SumulatedMarketMaker.SinulatedGateLiveDummyExchange import SimulatedGateLiveDummyExchange
from marketmaker.KillSwitch import KillSwitch
from marketmaker.MarketMakerGui import MarketMakerGui
from Test.SumulatedMarketMaker.SimulatedExchange import SimulatedExchange
from connectivity.LocalOrderBookBase import LocalOrderBookBase, OrderBookEntry, OrderBook
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Coin, Instruments, Instrument
from marketmaker.RiskManager import RiskManager
from marketmaker.Strategy import GlobalRiskLimit
from marketmaker.QuoteManager import QuoteManager

logging.basicConfig(level=logging.ERROR, format=Static.LOGFORMAT,
                    handlers=[logging.FileHandler(Static.logFile, mode='w'),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def dummy(rm: RiskManager, instrument:Instrument, exchangeManager: SimulatedExchange):
    flag = -1
    while True:
        await asyncio.sleep(60)
        amount: Decimal = GlobalRiskLimit
        amount = amount + 150
        midPrice = exchangeManager.localOrderBooks[instrument].midTob
        RiskManager.risks[Coin.UX].position = flag * Decimal(amount / midPrice)
        RiskManager.risks[Coin.UX].positionValue = amount
        flag = flag*-1
        logger.debug("Generated dummy trade")
        await asyncio.sleep(300)

if __name__ == '__main__':
    logger.info("starting up")

    conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
    instruments:List[Instrument] = list()
    instrument = Instruments.instruments["UMEE_USDT"]
    instruments.append(instrument)

    pnlCoin = Coin.USDT
    coins = [instrument.base for instrument in instruments]

    #exchangeManager = SimulatedExchange(instruments, conn)
    exchangeManager = SimulatedGateLiveDummyExchange(instruments, conn)
    quoteManager = QuoteManager(instrument, exchangeManager)
    localOrderBooks = {}
    [localOrderBooks.update({instrument.base: exchangeManager.localOrderBooks[instrument]}) for instrument in instruments]
    usdtLocalOrderBook = LocalOrderBookBase(instrument, asyncio.Queue())
    bids:SortedList = SortedList(key=lambda x: -x.price)
    bids.add(OrderBookEntry(1, 100000))
    asks:SortedList = SortedList()
    asks.add(OrderBookEntry(1, 100000))
    usdtLocalOrderBook.ob = OrderBook(instrument, "id1", bids, asks)
    localOrderBooks[Coin.USDT] = usdtLocalOrderBook

    rm: RiskManager = RiskManager(coins, pnlCoin, localOrderBooks)
    quoteManager.initialize()
    exchangeManager.initialize()


    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    killSwitch: KillSwitch = KillSwitch(loop)

    loop.create_task(quoteManager.run())
    loop.create_task(exchangeManager.run())
    loop.create_task(exchangeManager.runMyOrderUpdate())
    loop.create_task(conn.run())
    loop.create_task(killSwitch.run())
    loop.create_task(dummy(rm,instrument, exchangeManager))
    marketMakerGui: MarketMakerGui = MarketMakerGui(loop, quoteManager)
    loop.run_forever()

    loop.close()
