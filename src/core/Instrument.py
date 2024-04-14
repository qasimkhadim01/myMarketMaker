class Coin:
    UX = "UMEE"
    USDT = "USDT"
    BTC = "BTC"


class Instrument:
    def __init__(self, base, counter):
        self.base = base
        self.counter = counter

    def __str__(self):
        return str(self.base + "_" + self.counter).upper()


class Instruments:
    instruments = {"UMEE_USDT": Instrument(Coin.UX, Coin.USDT),
                   "BTC_USDT": Instrument(Coin.BTC, Coin.USDT),
                   "USDT_USDT": Instrument(Coin.BTC, Coin.USDT)
                   }
