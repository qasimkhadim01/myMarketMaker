from decimal import Decimal

import math

def roundUp(number: float, decimals:int):
    roundedNumber = math.ceil(number)
    factor = 10**decimals
    return math.ceil(roundedNumber*factor)/factor



def instrRound(number, precision):
    round(Decimal(number / (10 ** precision)), precision)

def roundDown(number:Decimal, decimals:int):
    roundedNumber = math.floor(number)
    factor = 10**decimals
    return math.floor(roundedNumber*factor)/factor

