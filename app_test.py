import time
import threading
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import warnings

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import BarData

class TradingApp(EClient, EWrapper):

    def __init__(self) -> None:

        EClient.__init__(self, self)
        self.data: Dict[int, pd.DataFrame] = {}
        self.nextOrderId: Optional[int] = None

    def error(self, reqId: int, errorCode: int, errorString: str) -> None:

        print(f"Error: {reqId}, {errorCode}, {errorString}")

    def nextValidId(self, orderId: int) -> None:

        super().nextValidId(orderId)
        self.nextOrderId = orderId

    def get_historical_data(self, reqId: int, contract: Contract) -> pd.DataFrame:

        self.data[reqId] = pd.DataFrame(columns=["time", "high", "low", "close"])
        self.data[reqId].set_index("time", inplace=True)
        self.reqHistoricalData(
            reqId=reqId,
            contract=contract,
            endDateTime="",
            durationStr="1 D",
            barSizeSetting="1 min",
            whatToShow="MIDPOINT",
            useRTH=0,
            formatDate=2,
            keepUpToDate=False,
            chartOptions=[],
        )
        time.sleep(5)
        return self.data[reqId]

    def historicalData(self, reqId: int, bar: BarData) -> None:

        df = self.data[reqId]

        df.loc[
            pd.to_datetime(bar.date, unit="s"), 
            ["high", "low", "close"]
        ] = [bar.high, bar.low, bar.close]

        df = df.astype(float)

        self.data[reqId] = df

    @staticmethod
    def get_contract(symbol: str) -> Contract:

        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def place_order(self, contract: Contract, action: str, order_type: str, quantity: int) -> None:

        order = Order()
        order.action = action
        order.orderType = order_type
        order.totalQuantity = quantity

        self.placeOrder(self.nextOrderId, contract, order)
        self.nextOrderId += 1
        print("Order placed")


app = TradingApp()

app.connect("127.0.0.1", 7497, clientId=5)

threading.Thread(target=app.run, daemon=True).start()

while True:
    if isinstance(app.nextOrderId, int):
        print("connected")
        break
    else:
        print("waiting for connection")
        time.sleep(1)


nvda = TradingApp.get_contract("NVDA")

data = app.get_historical_data(99, nvda)
data.tail()