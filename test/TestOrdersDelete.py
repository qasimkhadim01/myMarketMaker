import json
import time
from websocket import create_connection
import asyncio

async def cancelOrder():
    cancelParam = {"order_id": "1694883366", "currency_pair": "GT_USDT"}
    channel = "spot.order_cancel"

    ws = create_connection("wss://api.gateio.ws/ws/v4/")

    ws.send(json.dumps({
        "time": int(time.time()),
        "channel": channel,
        "event": "api",
        "payload": {
            "req_id": "test_1",
            "req_param": cancelParam
        }
    }))

    print(ws.recv())
