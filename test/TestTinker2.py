import tkinter as tk
from tkinter import END
from typing import List


class Gui:
    def __init__(self):
        root = tk.Tk()
        root.geometry("1200x1000")
        self.depth = 5

        frameUpper = tk.Frame(root)
        frameLower = tk.Frame(root)
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
            label.grid(column=3, row=i, sticky=tk.W, padx=5, pady=5)
            labelAmount = tk.Label(frameUpperLhs, text="askVol" + str(i))
            labelAmount.grid(column=4, row=i, sticky=tk.W, padx=5, pady=5)
            self.askPrice.append(label)
            self.askAmount.append(labelAmount)
            space = tk.Label(frameUpper, text="    ")
            space.grid(column=5, row=i, sticky=tk.W, padx=20, pady=5)


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
        self.textTicketSize = tk.Label(frameUpperRhs2, text="ticket size")
        self.textTicketSize.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        labelDebug = tk.Label(frameUpperRhs2, text="Debug")
        labelDebug.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.textDebug = tk.Label(frameUpperRhs2, text="level")
        self.textDebug.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        exitButton = tk.Button(frameUpperRhs2, text="Exit")
        exitButton.grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)


        labelExecutions = tk.Label(frameLower, text="Executions")
        labelExecutions.grid(row=0, column=0, pady=10, sticky=tk.W)


        yScroll = tk.Scrollbar(frameLower, orient=tk.VERTICAL)
        yScroll.grid(row=1, column=1, sticky=tk.NW+tk.S)
        xScroll = tk.Scrollbar(frameLower, orient=tk.HORIZONTAL)
        xScroll.grid(row=2, column=0, sticky=tk.E+tk.W)
        self.listbox = tk.Listbox(frameLower, xscrollcommand=xScroll.set, yscrollcommand=yScroll.set, width=70)
        self.listbox.grid(row=1, column=0, sticky=tk.W)
        xScroll['command'] = self.listbox.xview
        yScroll['command'] = self.listbox.yview

        # Launch the GUI
        root.mainloop()

gui = Gui()