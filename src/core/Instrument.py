class Coin:
    UX = "UMEE"
    USDT = "USDT"
    BTC = "BTC"
    ETH = "ETH"
    XRP = "XRP"

class Instrument:
    def __init__(self, base, counter, amountPrecision = 2, pricePrecision =5 ):
        self.base = base
        self.counter = counter
        self.amountPrecision = amountPrecision
        self.pricePrecision = pricePrecision

    def __str__(self):
        return str(self.base + "_" + self.counter).upper()


class Instruments:
    instruments = {"UMEE_USDT": Instrument(Coin.UX, Coin.USDT, 6, 6),
                   "BTC_USDT": Instrument(Coin.BTC, Coin.USDT,  6, 2),
                   "ETH_USDT": Instrument(Coin.ETH, Coin.USDT, 6, 2),
                   "XRP_USDT": Instrument(Coin.XRP, Coin.USDT),
                   "USDT_USDT": Instrument(Coin.USDT, Coin.USDT)
                   }
