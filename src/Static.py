from core.Instrument import Coin, Instrument, Instruments

myApiKeyObsolete = "f4a64af3ff9c584d39395fa1c4477026"
mySecretKeyObsolete = "2c70a4f598daf7feb6c60fdfdb6a9834549933fba65e21ded9cb1389558269b2"
gateioCollectorFile = "c:\\Users\\qasim\\Projects\\tickdata\\gateio\\"
#logFile = "C:\\Users\\qasim\\Projects\\temp\\UMEE.log"
logFile = "UMEE.log"
LOGFORMAT = "[%(asctime)s:%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
KeepRunning = True
KillInstrument = Instruments.instruments.get(str(Instrument(Coin.XRP, Coin.USDT)))
Kill = False
