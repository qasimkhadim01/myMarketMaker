from datetime import datetime
import pandas as pd
import numpy as np
from enum import Enum

class InterpolationMethog(Enum):
    Previous =1,
    Next =2,
    Linear = 3

class TimeSeries:
    def __init__(self, name):
        self.name = name
        dataDefinition = {
            'timestamp' : np.ndarray((0,), np.dtype('datetime64[ns]')),
            'value' : np.ndarray((0,), np.float64)
        }
        self.df = pd.DataFrame(dataDefinition)
    def add(self, timestamp, value):
        newRow = {'timestamp' : timestamp, 'value' : value}
        self.df.loc[len(self.df)] = newRow

    def min(self):
        self.df['value'].min()
    def max(self):
        self.df['value'].max()
    def first(self):
        self.df.iloc[0]
    def interpolate(self, searchDate, interpolationMethod):
        if searchDate in self.df['timestamp'].values:
            return self.df[self.df['timestamp']==searchDate].iloc[0,0]
        idx = self.df.index.get_loc(searchDate, 'nearest')
        value = None
        match interpolationMethod:
            case InterpolationMethod.Previous:
                value = self.df.iloc[idx,'value']
            case InterpolationMethod.Next:
                value = self.df.iloc[idx+1, 'value']
            case InterpolationMethog.Linear:
                deltaTime = self.df.iloc[idx+1, 'timestamp']-self.df.iloc[idx, 'timestamp']
                fractionalTime = (searchDate - self.df.iloc[idx, 'value']*deltaTime)
                deltaValue = self.df.ilic[idx+1, 'value'] - self.df.iloc[idx, 'value']
                value = self.df.iloc[idx, 'value'] + fractionalTime*deltaValue

        return value
