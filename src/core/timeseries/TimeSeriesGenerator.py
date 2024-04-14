import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from enum import Enum

from src.estimator.volatility.TwoScaleVarEstimator import TwoScaleVarEstimator
from src.timseries.TimeSeries import TimeSeries


class BownianMotion(Enum):
    Geometric=1,
    Arithmetic=2


class InterpolationMethod:
    pass


class TimeSeriesGenerator:
    @staticmethod
    def generateConstantVolSeries(startTime, constVol, sampleCount, samplingIntervalSec):
        ts = TimeSeries("Constant Vol Series")
        timestamp = startTime
        for sampleIndex in range(0,sampleCount):
            ts.add(timestamp, constVol)
            timestamp += timedelta(seconds=samplingIntervalSec)
        return ts

    @staticmethod
    def generatePriceSeries(volSeries, startingPrice, relativeNoiseVol, brownianMotion, muDrift):
        tsSimulatePrice = TimeSeries("Simulated Price Series")
        tsRandomVars = TimeSeries("Gaussians")
        for idx,row in volSeries.df.iterrows():
             tsRandomVars.add(row.timestamp,random.gauss(0,1))

        accumSigmadW = 0
        drift=0

        first = True
        noiseyAssetPrice = TimeSeriesGenerator.addMicrostructureNoise(relativeNoiseVol, startingPrice)
        prevItem = None
        for idx,item in tsRandomVars.df.iterrows():
            if first:
                tsSimulatePrice.add(item.timestamp, noiseyAssetPrice)
                prevItem=item
                first = False
                continue
            timeIncr = (item['timestamp']-prevItem['timestamp']).total_seconds()
            vol = volSeries.interpolate(item['timestamp'], InterpolationMethod.Previous)
            accumSigmadW += vol*item["value"]*np.sqrt(timeIncr)

            trueAssetPrice =0
            match(brownianMotion):
                case BownianMotion.Geometric:
                    drift+=0.5*np.power(vol,2)*timeIncr
                    if muDrift is not None:
                        trueAssetPrice = startingPrice*np.exp(accumSigmadW) - drift + (muDrift.integratedRetun(item['timestamp']),volSeries.first()['timestamp'])
                    else:
                        trueAssetPrice = startingPrice*np.exp(accumSigmadW)-drift
                case BownianMotion.Arithmetic:
                    if muDrift is not None:
                        trueAssetPrice = startingPrice+accumSigmadW + muDrift.integratedRetun(item['timeStamp']),volSeries.first()['timestamp']
                    else:
                        trueAssetPrice = startingPrice + accumSigmadW
            noiseyAssetPrice = TimeSeriesGenerator.addMicrostructureNoise(relativeNoiseVol, trueAssetPrice)
            tsSimulatePrice.add(item['timestamp'], noiseyAssetPrice)
        return tsSimulatePrice

    @staticmethod
    def addMicrostructureNoise(noiseVol, trueAssetPrice):
        noiseyAssetPrice = trueAssetPrice
        if noiseVol is not None and noiseVol > 0:
            gaussianVariate = random.gauss();
            logNoiseyAssetPrice = np.log(trueAssetPrice) + gaussianVariate*noiseVol
            noiseyAssetPrice = np.exp(logNoiseyAssetPrice)
        return noiseyAssetPrice


if __name__ == '__main__':

    df = pd.read_csv("D:\\projects\\code\\Python\\MMLP\\data.csv", header=None)
    volEstimator = TwoScaleVarEstimator(350, 5)
    priceSeries = TimeSeries("price")

    for idx, row in df.iterrows():
        priceSeries.add(datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f'),row[1])


    theVols = volEstimator.realizedVol(priceSeries)
    print(theVols)



    volSeries = TimeSeriesGenerator.generateConstantVolSeries(datetime.now(), 0.005, 1000, 5)
    priceSeries = TimeSeriesGenerator.generatePriceSeries(volSeries,
                                                          1.0, None,BownianMotion.Geometric, None )

    volEstimator = TwoScaleVarEstimator(350, 5)
    theVols = volEstimator.realizedVol(priceSeries)

