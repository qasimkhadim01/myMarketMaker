import logging

from connectivity.gateio.GateIOManager import GateIOManager
from connectivity.gateio import Api
from connectivity.gateio.ws import Connection, Configuration
from core.Instrument import Instruments
from core.MyEnums import OrderSide
from core.Orders import SpotLimitOrder, SpotMarketOrder
from decimal import Decimal

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s: %(message)s")
logger = logging.getLogger()

conn = Connection(Configuration(api_key=Api.API_KEY, api_secret=Api.SECRET_KEY))
sInstrument = "UMEE_USDT"
instrument = Instruments.instruments.get(sInstrument )
amount = Decimal(5)
price = Decimal(0.004)


# exchangeManager = SimulatedExchange(instrument, conn)
exchangeManager = GateIOManager(sInstrument, conn)
marketOrder = SpotMarketOrder(id="t-qmarket_1", instrument=instrument, side=OrderSide.Buy, amount = amount)
exchangeManager.sendMarketOrder(marketOrder)

# limitOrder = SpotLimitOrder(id="t-qlimit_1", instrument=instrument, side=OrderSide.Buy, amount=amount, price=price)
# exchangeManager.sendLimitOrder(limitOrder)
# limitOrder.price = price = Decimal(0.0035)
# exchangeManager.amendLimitOrder(limitOrder)
# exchangeManager.cancelLimitOrder(limitOrder)
