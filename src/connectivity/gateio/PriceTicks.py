import gate_api
from gate_api.exceptions import ApiException, GateApiException
import pandas as pd
import time
import datetime as dt


def appendDataToDf(priceBefore, data, ts):
    volume = data.base_volume
    price = pd.to_numeric(data.last)
    priceDelta = price - priceBefore
    priceDeltaP = 0

    if price > 0:
        priceCeltaP = priceDelta / price

    newRecord = {
        'Symbol': data.currency_pair,
        'Timestamp': ts,
        'Volume': volume,
        'Price': price,
        'PriceDelta': priceDelta,
        'PriceDeltaPercent': priceDeltaP
    }
    return newRecord


def requestData(runs, currencyPair, s):
    currencyDfs = {}
    apiResponse = None
    for t in range(runs):
        try:
            apiResponse = apiInstance.list_tickers(currency_pair=currencyPair)
        except GateApiException as ex:
            print("Gate Api exceptiom, label :%s, message:%s \n", (ex.label, ex.message))
        except ApiException as e:
            print ("Exception when calling SpotApi->list_tickers: %s\n", e)

        ts = dt.datetime.now()
        currencyResponseDict = {resp.currency_pair: resp for resp in apiResponse
                if "USDT" in resp.currency_pair and "BEAR" not in resp.currency_pair}

        for currencyName, response in currencyResponseDict.items():
            if currencyName not in currencyDfs:
                currencyDfs[currencyName]=pd.DataFrame(columns=[
                    'Symbol',
                    'Timestamp',
                    'Volume',
                    'Price',
                    'PriceDelta',
                    'PriceDeltaPercent'])
            if len(currencyDfs[currencyName]) > 1:
                priceBefore = currencyDfs[currencyName]['Price'].iloc[-1]
            else:
                priceBefore = 0

            newDataAsDict = appendDataToDf(priceBefore, response, ts)
            currencyDfs[currencyName].loc[len(currencyDfs[currencyName].index)] = newDataAsDict
            time.sleep(s)
    return currencyDfs


configuration = gate_api.Configuration(host="https://api.gateio.ws/api/v4")
apiClient = gate_api.ApiClient(configuration)
apiInstance = gate_api.SpotApi(apiClient)

s=1
currencyPair = ''
runs = 4
dfList = requestData(runs, currencyPair, s)

