import bisect
import copy
import logging
import tkinter as tk
from bisect import insort
from decimal import Decimal
from tkinter import ttk
import time
from typing import List
import asyncio

from sortedcontainers import SortedList, SortedKeyList

import Static
from connectivity.LocalOrderBookBase import LocalOrderBookBase, OrderBookEntry
from core.Utils import roundDown
from marketmaker.RiskManager import RiskManager
from marketmaker.Strategy import MultiRandomStrategy, DefensiveStrategy, \
    LadderStrategy, JoinStrategy, Strategy, liveStrategies, GlobalRiskLimit
from marketmaker.QuoteManager import QuoteManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
Static.appLoggers.append(logger)


class MarketMakerGui(tk.Tk):

    def updateLogLevel(self):
        level = self.logLevel.get()
        for theLogger in Static.appLoggers:
            if level == "DEBUG":
                theLogger.setLevel(logging.DEBUG)
            elif level == "ERROR":
                theLogger.setLevel(logging.ERROR)
            elif level == "INFO":
                theLogger.setLevel(logging.INFO)
            else:
                theLogger.setLevel(logging.DEBUG)
        logger.error("Open orders...")
        [logger.error(order) for order in self.quoteManager.myBids]

    def __init__(self, loop, quoteManager: QuoteManager):
        super().__init__()

        self.riskLimit: tk.StringVar = tk.StringVar()
        self.quoteManager = quoteManager
        self.localOrderBook: LocalOrderBookBase = self.quoteManager.exchangeManager.localOrderBooks[self.quoteManager.instrument]
        self.depth: int = 10
        self.bidPrice: List[tk.Label] = list()
        self.bidAmount: List[tk.Label] = list()
        self.askPrice: List[tk.Label] = list()
        self.askAmount: List[tk.Label] = list()
        self.loop = loop
        self.geometry("1600x1000")
        self.title('Order Book')
        self.startTime = int(time.time())
        self.pricePrecision = self.localOrderBook.instrument.pricePrecision
        self.amountPrecision = self.localOrderBook.instrument.amountPrecision
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.tasks = []
        self.tasks.append(loop.create_task(self.updateGui()))

        colors: list[str] = ["red", "lime green", "blue",  "purple", "yellow"]
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
            labelPrice = tk.Label(frameUpperLhs, text="bid" + str(i))
            labelPrice.grid(column=0, row=i, sticky=tk.W, padx=5, pady=5)
            labelAmount = tk.Label(frameUpperLhs, text="bidvol" + str(i))
            labelAmount.grid(column=1, row=i, sticky=tk.W, padx=5, pady=5)

            self.bidPrice.append(labelPrice)
            self.bidAmount.append(labelAmount)

        for i in range(self.depth):
            label = tk.Label(frameUpperLhs, text="ask" + str(i))
            label.grid(column=2, row=i, sticky=tk.W, padx=5, pady=5)
            labelAmount = tk.Label(frameUpperLhs, text="askVol" + str(i))
            labelAmount.grid(column=3, row=i, sticky=tk.W, padx=5, pady=5)
            self.askPrice.append(label)
            self.askAmount.append(labelAmount)

        labelObTs = tk.Label(frameUpperRhs1, text="OB ts")
        labelObTs.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.textObTs = tk.Label(frameUpperRhs1, text="timestamp")
        self.textObTs.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        labelTobTs = tk.Label(frameUpperRhs1, text="TOB ts")
        labelTobTs.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.textTobTs = tk.Label(frameUpperRhs1, text="timestamp")
        self.textTobTs.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        labelRiskLimit = tk.Label(frameUpperRhs1, text="RiskLimit")
        labelRiskLimit.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        #def callback(sv):
        #    Strategy.GlobalRiskLimit = sv.get()
        #    logger.error(f"global risk limit updated {Strategy.GlobalRiskLimit}")

        self.riskLimit.set(GlobalRiskLimit)
        #self.riskLimit.trace("w", lambda name, index, mode, sv=riskLimit: callback(riskLimit))
        textRiskLimit = tk.Entry(frameUpperRhs1, textvariable=self.riskLimit)
        textRiskLimit.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

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

#        labelTicketSize = tk.Label(frameUpperRhs2, text="ticket size")
#        labelTicketSize.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
#        self.textTicketSize = tk.Label(frameUpperRhs2, text="100")
#        self.textTicketSize.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        labelLogLevel = tk.Label(frameUpperRhs2, text="logLevel")
        labelLogLevel.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.logLevel = ttk.Combobox(frameUpperRhs2, state="readonly", values=["DEBUG", "INFO", "ERROR"])
        self.logLevel.set("DEBUG")
        self.logLevel.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.logLevel.bind("<<ComboboxSelected>>", lambda x: self.updateLogLevel())

        exitButton = tk.Button(frameUpperRhs2, text="Exit", command=self.quit)
        exitButton.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        labelExecutions = tk.Label(frameLower, text="Executions")
        labelExecutions.grid(row=0, column=0, pady=10, sticky=tk.W)

        yScroll = tk.Scrollbar(frameLower, orient=tk.VERTICAL)
        yScroll.grid(row=1, column=1, sticky=tk.NW + tk.S)
        xScroll = tk.Scrollbar(frameLower, orient=tk.HORIZONTAL)
        xScroll.grid(row=2, column=0, sticky=tk.E + tk.W)
        self.listbox = tk.Listbox(frameLower, xscrollcommand=xScroll.set, yscrollcommand=yScroll.set, width=150)
        self.listbox.grid(row=1, column=0, sticky=tk.W)
        xScroll['command'] = self.listbox.xview
        yScroll['command'] = self.listbox.yview

        # self.modelOrderBook(frameUpper)

    async def updateGui(self):
        while Static.KeepRunning:
            await asyncio.sleep(0.5)

            try:
                self.textPosition.config(
                    text=f"{RiskManager.risks[self.quoteManager.instrument.base].positionValue:.0f}")
                # self.textRiskLimit.config(text=f"{RiskParam.RiskLimit.value}")
                timeStamp = self.localOrderBook.obTimeStamp.strftime("%H:%M:%S")
                self.textObTs.config(text=f"{timeStamp}")
                timeStamp = self.localOrderBook.tobTimeStamp.strftime("%H:%M:%S")
                self.textTobTs.config(text=f"{timeStamp}")

                def update(book:SortedList, entry:OrderBookEntry):
                    try:
                        idx = book.index(entry)
                    except ValueError:
                        # price not found, insert it
                        book.add(entry)

                #ob = copy.deepcopy(self.localOrderBook.ob)
                #[ob.update_entry(ob.bids ,OrderBookEntry(order.price, order.amount), False) for order in self.quoteManager.myBids.values()]
                #[ob.update_entry(ob.asks ,OrderBookEntry(order.price, order.amount), False) for order in self.quoteManager.myAsks.values()]

                obBids: SortedList = SortedList(key=lambda x: -x.price)
                obAsks: SortedList = SortedList()
                [obBids.add(entry) for entry in self.localOrderBook.ob.bids[:20]]
                [obAsks.add(entry) for entry in self.localOrderBook.ob.asks[:20]]

                [update(obBids ,OrderBookEntry(order.price, order.amount)) for order in self.quoteManager.myBids.values()]
                [update(obAsks ,OrderBookEntry(order.price, order.amount)) for order in self.quoteManager.myAsks.values()]


                for i in range(len(self.bidPrice)):
                    self.bidPrice[i].config(text=f"{obBids[i].price:.{self.pricePrecision}f}",
                                            fg="black")
                    self.bidAmount[i].config(text=f"{obBids[i].amount:.{self.amountPrecision}f}")

                for i in range(len(self.askPrice)):
                    self.askPrice[i].config(text=f"{obAsks[i].price:.{self.pricePrecision}f}",
                                            fg="black")
                    self.askAmount[i].config(text=f"{obAsks[i].amount:.{self.amountPrecision}f}")

                for strategy in liveStrategies:
                    strategyBids = [order for order in self.quoteManager.myBids.values() if order.strategy == strategy]
                    if len(strategyBids) > 0: logger.debug(f"strategy {strategy.__class__.__name__} bids found {len(strategyBids)} strategy={round(strategyBids[0].price, self.pricePrecision)} OB={round(self.localOrderBook.ob.bids[0].price, self.pricePrecision)}")
                    strategyAsks = [order for order in self.quoteManager.myAsks.values() if order.strategy == strategy]
                    if len(strategyAsks) > 0: logger.debug(f"strategy {strategy.__class__.__name__} asks found {len(strategyAsks)} strategy={round(strategyAsks[0].price, self.pricePrecision)} OB={round(self.localOrderBook.ob.asks[0].price, self.pricePrecision)}")

                    matches = [i for i, item in enumerate(obBids) if
                               item.price in [x.price for x in strategyBids]]

                    [self.bidPrice[i].config(fg=self.strategyColours[strategy]) for i in matches if
                     i < len(self.bidPrice)]

                    matches = [i for i, item in enumerate(obAsks) if
                               item.price in [x.price for x in strategyAsks]]

                    [self.askPrice[i].config(fg=self.strategyColours[strategy]) for i in matches if
                     i < len(self.askPrice)]

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
                Strategy.GlobalRiskLimit = self.riskLimit.get()
                self.update()

            except:
                logger.exception('')
                logger.error(
                    f"local order book size bids={len(self.localOrderBook.ob.bids)} asks={len(self.localOrderBook.ob.asks)}")
        logging.error("Kill Switch Triggered")
        # self.close()

    def modelOrderBook(self, frame):
        a = 1
        if a == 1: return
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
        Static.Kill = True
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]

        self.loop.run_until_complete(asyncio.gather(*tasks))
        self.loop.stop()
        self.destroy()
