from numpy import *
import pandas as pd

def calcHurst(ts):
    lags = range(2,20)
    for lag in lags:
        q = subtract(ts[lag:], ts[:-lag])
        z= std(q)
        print(lag)

    tau = [sqrt(std(subtract(ts[lag:], ts[:lag]))) for lag in lags]
    #plot on logscale
    #calculate hurst as slope of log-log plot
    m = polyfit(log(lags), log(tau), 1)
    hurst = m[0]*2.0
    return hurst

ts = [0]
#for i in range(1,1000):
#   ts.append(ts[i-1]*1.0*random.rand())
ts = pd.read_csv("hurst.csv")
calcHurst(ts)