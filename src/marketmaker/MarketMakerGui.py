import logging
import tkinter as tk
import time
from typing import List
import asyncio

import Static
from connectivity.LocalOrderBookBase import LocalOrderBookBase
from marketmaker.RiskManager import RiskManager
from marketmaker.Strategy import MultiRandomStrategy, DefensiveStrategy, \
    MultiLadderStrategy, JoinStrategy, RiskParam, Strategy, liveStrategies
from marketmaker.QuoteManager import QuoteManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class MarketMakerGui(tk.Tk):
    def __init__(self, loop, quoteManager: QuoteManager):
        super().__init__()
        self.quoteManager = quoteManager
        self.localOrderBook: LocalOrderBookBase = self.quoteManager.exchangeManager.localOrderBook
        self.depth: int = 10
        self.bidPrice: List[tk.Label] = list()
        self.bidAmount: List[tk.Label] = list()
        self.askPrice: List[tk.Label] = list()
        self.askAmount: List[tk.Label] = list()
        self.loop = loop
        self.geometry("1200x1000")
        self.title('Order Book')
        self.startTime = int(time.time())
        self.pricePrecision = self.localOrderBook.instrument.pricePrecision
        self.amountPrecision = self.localOrderBook.instrument.amountPrecision
        self.create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.tasks = []
        self.tasks.append(loop.create_task(self.updateGui()))

        colors: list[str] = ["red", "blue", "dark green", "purple", "yellow"]
        self.strategyColours: dict[Strategy: str] = dict()
        for i in range(len(liveStrategies)):
            self.strategyColours[liveStrategies[i]] = colors[i]

    def quit(self):
        Static.Kill = True

    def create_widgets(self):
        frameUpper = tk.Frame(self)
        frameLower = tk.Frame(self)
        frameUpperLhs = tk.Frame(frameUpper)
        frameUpperRhs = tk.Frame(frameUpper)
        frameUpperRhs1 = tk.Frame(frameUpperRhs)
        frameUpperRhs2 = tk.Frame(frameUpperRhs)

        frameUpper.grid(row=0, column=0, padx=50)
        frameUpperLhs.grid(row=0, column=0, padx=50)
        frameUpperRhs.grid(row=0, column=1, padx=50)
        frameUpperRhs1.grid(row=0, column=0, padx=50)
        frameUpperRhs2.grid(row=1, column=0, padx=50)
        frameLower.grid(row=1, column=0, pady=50)


        self.bidPrice: List[tk.Label] = list()
        self.bidAmount: List[tk.Label] = list()
        self.askPrice: List[tk.Label] = list()
        self.askAmount: List[tk.Label] = list()
        for i in range(self.depth):
            labelPrice = tk.Label(frameUpperLhs, text="bid"+str(i))
            labelPrice.grid(column=0, row=i, sticky=tk.W, padx=5, pady=5)
            labelAmount = tk.Label(frameUpperLhs, text="bidvol"+str(i))
            labelAmount.grid(column=1, row=i, sticky=tk.W, padx=5, pady=5)

            self.bidPrice.append(labelPrice)
            self.bidAmount.append(labelAmount)

        for i in range(self.depth):
            label = tk.Label(frameUpperLhs, text="ask"+str(i))
            label.grid(column=2, row=i, sticky=tk.W, padx=5, pady=5)
            labelAmount = tk.Label(frameUpperLhs, text="askVol" + str(i))
            labelAmount.grid(column=3, row=i, sticky=tk.W, padx=5, pady=5)
            self.askPrice.append(label)
            self.askAmount.append(labelAmount)


        labelTs = tk.Label(frameUpperRhs1, text="timestamp")
        labelTs.grid(row=0, column=0,  sticky=tk.W, padx=5, pady=5)
        self.textTs = tk.Label(frameUpperRhs1, text="timestamp")
        self.textTs.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        labelPrescence = tk.Label(frameUpperRhs1, text="Prescence")
        labelPrescence.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.textPrescence = tk.Label(frameUpperRhs1, text="Prescence")
        self.textPrescence.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        labelRiskLimit = tk.Label(frameUpperRhs1, text="RiskLimit")
        labelRiskLimit.grid(row=1, column=0,  sticky=tk.W, padx=5, pady=5)
        self.textRiskLimit = tk.Label(frameUpperRhs1, text="Risk LImit")
        self.textRiskLimit.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        labelPosition = tk.Label(frameUpperRhs1, text="UsdT Position")
        labelPosition.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.textPosition = tk.Label(frameUpperRhs1, text="USD Position")
        self.textPosition.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        labelRealizedPnl = tk.Label(frameUpperRhs1, text="Realized Pnl")
        labelRealizedPnl.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.textRealizedPnl = tk.Label(frameUpperRhs1, text="0")
        self.textRealizedPnl.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        labelUnRealizedPnl = tk.Label(frameUpperRhs1, text="UnRealized Pnl")
        labelUnRealizedPnl.grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.textUnRealizedPnl = tk.Label(frameUpperRhs1, text="0")
        self.textUnRealizedPnl.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        labelTicketSize = tk.Label(frameUpperRhs2, text="ticket size")
        labelTicketSize.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.textTicketSize = tk.Label(frameUpperRhs2, text="100")
        self.textTicketSize.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        labelDebug = tk.Label(frameUpperRhs2, text="Debug")
        labelDebug.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.textDebug = tk.Label(frameUpperRhs2, text="level")
        self.textDebug.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        exitButton = tk.Button(frameUpperRhs2, text="Exit", command=self.quit)
        exitButton.grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)


        labelExecutions = tk.Label(frameLower, text="Executions")
        labelExecutions.grid(row=0, column=0, pady=10, sticky=tk.W)

        yScroll = tk.Scrollbar(frameLower, orient=tk.VERTICAL)
        yScroll.grid(row=1, column=0, sticky=tk.NW + tk.S)
        xScroll = tk.Scrollbar(frameLower, orient=tk.HORIZONTAL)
        xScroll.grid(row=2, column=0, sticky=tk.E + tk.W)
        self.listbox = tk.Listbox(frameLower, xscrollcommand=xScroll.set, yscrollcommand=yScroll.set, width=80)
        self.listbox.grid(row=1, column=0, sticky=tk.W)
        xScroll['command'] = self.listbox.xview
        yScroll['command'] = self.listbox.yview

        # self.modelOrderBook(frameUpper)

    async def updateGui(self):
        while Static.KeepRunning:
            await asyncio.sleep(2)

            try:
                self.textPosition.config(
                    text=f"{RiskManager.risks[self.quoteManager.instrument.base].positionValue:.0f}")
                self.textRiskLimit.config(text=f"{RiskParam.RiskLimit.value}")
                timeStamp = self.localOrderBook.timestamp.strftime("%H:%M:%S")
                self.textTs.config(text=f"{timeStamp}")

                for i in range(len(self.bidPrice)):
                    self.bidPrice[i].config(text=f"{self.localOrderBook.ob.bids[i].price:.{self.pricePrecision}f}",
                                            fg="black")
                    self.bidAmount[i].config(text=f"{self.localOrderBook.ob.bids[i].amount}")

                for i in range(len(self.askPrice)):
                    self.askPrice[i].config(text=f"{self.localOrderBook.ob.asks[i].price:.{self.pricePrecision}f}",
                                            fg="black")
                    self.askAmount[i].config(text=f"{self.localOrderBook.ob.asks[i].amount}")


                for strategy in liveStrategies:
                    strategyBids = [order for order in self.quoteManager.myBids.values() if order.strategy == strategy]
                    if len(strategyBids) > 0: logger.debug(f"strategy {strategy} bids found {len(strategyBids)}")
                    strategyAsks = [order for order in self.quoteManager.myAsks.values() if order.strategy == strategy]
                    if len(strategyAsks) > 0: logger.debug(f"strategy {strategy} asks found {len(strategyAsks)}")

                    matches = [i for i, item in enumerate(self.localOrderBook.ob.bids) if
                               item.price in [x.price for x in strategyBids]]

                    [self.bidPrice[i].config(fg=self.strategyColours[strategy]) for i in matches if i < len(self.bidPrice)]

                    matches = [i for i, item in enumerate(self.localOrderBook.ob.asks) if
                               item.price in [x.price for x in strategyAsks]]

                    [self.askPrice[i].config(fg=self.strategyColours[strategy]) for i in matches if i < len(self.askPrice)]



                if len(self.quoteManager.executedOrders) > self.listbox.size():
                    self.listbox.insert(0, str(
                        self.quoteManager.executedOrders[self.listbox.size()]))

                multiBids = [order for order in self.quoteManager.myBids.values() if
                             isinstance(order.strategy, MultiRandomStrategy)]
                multiAsks = [order for order in self.quoteManager.myAsks.values() if
                             isinstance(order.strategy, MultiRandomStrategy)]

                for i in range(len(multiBids)):
                    self.modelBidPrice[i].config(text=f"{multiBids[i].price:.{self.pricePrecision}f}", fg="black")
                    self.modelBidAmount[i].config(text=f"{multiBids[i].amount:.{self.amountPrecision}f}")

                for i in range(len(multiAsks)):
                    self.modelAskPrice[i].config(text=f"{multiAsks[i].price:.{self.pricePrecision}f}", fg="black")
                    self.modelAskAmount[i].config(text=f"{multiAsks[i].amount:.{self.amountPrecision}f}")

                self.textRealizedPnl.config(text=f"{RiskManager.realizedPnl():.2f}", fg="black")
                self.textUnRealizedPnl.config(text=f"{RiskManager.unRealizedPnl():.2f}", fg="black")
                self.update()

            except:
                logger.exception('')
                logger.error(f"local order book size bids={len(self.localOrderBook.ob.bids)} asks={len(self.localOrderBook.ob.asks)}")
        logging.error("Kill Switch Triggered")
        # self.close()

    def modelOrderBook(self, frame):
        a= 1
        if a==1: return
        labelMultiStrat = tk.Label(frame, text="MultiStrategy Order Boook")
        labelMultiStrat.grid(column=8, row=3, sticky=tk.W, padx=5, pady=5)
        self.modelBidPrice: List[tk.Label] = list()
        self.modelBidAmount: List[tk.Label] = list()
        self.modelAskPrice: List[tk.Label] = list()
        self.modelAskAmount: List[tk.Label] = list()
        for i in range(MultiRandomStrategy.nLevels):
            labelPrice = tk.Label(frame, text="Modelbid" + str(i))
            labelPrice.grid(column=6, row=i + 4, sticky=tk.W, padx=5, pady=5)
            labelAmount = tk.Label(frame, text="modelBidvol" + str(i))
            labelAmount.grid(column=7, row=i + 4, sticky=tk.W, padx=5, pady=5)

            self.modelBidPrice.append(labelPrice)
            self.modelBidAmount.append(labelAmount)

        for i in range(MultiRandomStrategy.nLevels):
            label = tk.Label(frame, text="modelAsk" + str(i))
            label.grid(column=8, row=i + 4, sticky=tk.W, padx=5, pady=5)
            labelAmount = tk.Label(frame, text="modelAskVol" + str(i))
            labelAmount.grid(column=9, row=i + 4, sticky=tk.W, padx=5, pady=5)
            self.modelAskPrice.append(label)
            self.modelAskAmount.append(labelAmount)

    def close(self):
        for task in self.tasks:
            task.cancel()
        self.loop.stop()
        self.destroy()
