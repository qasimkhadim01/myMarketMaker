import asyncio
import logging
from datetime import datetime
import pandas as pd

import Static
from connectivity.gateio.GateIOManager import GateIOManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Static.appLoggers.append(logger)


class OrderBookCollector():
    def __init__(self, orderBookTickStore, exchangeManager: GateIOManager):
        self.exchangeManager = exchangeManager
        self.collectorDf = None
        self.orderBookTickStore = orderBookTickStore
        self.initialize()

    async def update(self):
        while Static.KeepRunning:
            item = await self.exchangeManager.localOrderBookUpdateQueue.get()
            now = pd.to_datetime(datetime.now()).date()
            if len(self.collectorDf) > 0 :
                lastDate = pd.to_datetime(self.collectorDf[-1:].iloc[0,0]).date()
                if now != lastDate:
                    self.collectorDf.to_csv(
                        self.orderBookTickStore + "\\" + now.strftime("%m%d%Y") + "\\" + str(self.exchangeManager.localOrderBook.instrument) + ".csv")
                    self.initialize()

            for i in range(min(len(self.exchangeManager.localOrderBook.bids), len(self.exchangeManager.localOrderBook.asks))):
                newRow = {'timestamp': datetime.now().astimezone()
                    ,'bidPrice': self.exchangeManager.localOrderBook.bids[i].price
                    ,'bidSize': self.exchangeManager.localOrderBook.bids[i].amount
                    ,'askPrice': self.exchangeManager.localOrderBook.asks[i].price
                    ,'askSize': self.exchangeManager.localOrderBook.asks[i].amount}
                self.collectorDf.loc[len(self.collectorDf.index)] = newRow
            logging.error("Kill Switch Triggered")
            asyncio.get_event_loop().stop()

    def initialize(self):
        self.collectorDf = pd.DataFrame(columns=['timestamp', 'bidPrice', 'bidSize', 'askPrice', 'askSize'])
        self.collectorDf["timestamp"] = self.collectorDf["timestamp"].astype('datetime64[ns]')
        self.collectorDf['bidPrice'] = self.collectorDf['bidPrice'].astype('float')
        self.collectorDf['askPrice'] = self.collectorDf['askPrice'].astype('float')
        self.collectorDf['bidSize'] = self.collectorDf['bidSize'].astype('float')
        self.collectorDf['askSize'] = self.collectorDf['askSize'].astype('float')

    def release(self):
        self.collectorDf.to_csv(
            self.orderBookTickStore + "\\" + datetime.now().strftime("%d%m%Y") + "\\" + str(self.exchangeManager.instrument) + ".csv")