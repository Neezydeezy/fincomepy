from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
import math
from scipy.optimize import root

class FixedIncome(object):
    def __init__(self):
        return
    
    @staticmethod
    def perc_to_regular(percentage_values):
        return percentage_values*0.01

    @staticmethod
    def regular_to_perc(regular_values):
        return regular_values*100

class Bond(FixedIncome):
    def __init__(self, settlement, maturity, coupon_perc, price_perc, frequency, basis=1):
        ## TO DO: split clean price into 32nd
        self._settlement = settlement
        self._maturity = maturity
        self._coupon_perc = coupon_perc
        self._clean_price_perc = price_perc
        self._frequency = frequency
        self._basis = basis
        self._coupon_interval = 12 / frequency
        self._nperiod = math.ceil((self.diff_month(self._settlement, self._maturity))/self._coupon_interval)
        self._coupon_dates = [self._maturity - relativedelta(months=self._coupon_interval)*i for i in range(self._nperiod)]
        self._couppcd = self._maturity - relativedelta(months=self._coupon_interval)*(self._nperiod)
        self._coupncd = self._coupon_dates[-1]
        self._accrint = self.accrint(self._couppcd, self._coupncd, self._settlement, self._coupon_perc, 100, self._frequency, self._basis)
        self._dirty_price_perc = self._clean_price_perc + self._accrint

    def price(self, yield_perc): ## to do change function name to dirty price
        first_period = (self._coupncd - self._settlement).days / (self._coupncd - self._couppcd).days
        periods = np.array([first_period + i for i in range(self._nperiod)])
        CF_perc = np.array([self._coupon_perc / self._frequency] * self._nperiod)
        CF_perc[-1] += 100  ## change this to par
        CF_regular = FixedIncome.perc_to_regular(CF_perc)
        yield_regular = FixedIncome.perc_to_regular(yield_perc)
        DF = 1 / (1 + yield_regular / self._frequency) ** periods
        CF_PV_total = sum(CF_regular * DF)
        return FixedIncome.regular_to_perc(CF_PV_total)
    
    def get_yield(self):
        dirty_price_regular = FixedIncome.perc_to_regular(self._dirty_price_perc)
        print(dirty_price_regular)
        sol = root(lambda x: FixedIncome.perc_to_regular(self.price(x)) - dirty_price_regular, [0.01] )
        yield_perc = sol.x[0]
        return yield_perc

    @staticmethod
    def accrint(issue, first_interest, settlement, rate, par=100, frequency=2, basis=1):
        ## TO DO: change par=100
        ## TO DO: check if first_interest > issue
        total_days = (first_interest - issue).days
        accrued_days = (settlement - issue).days
        rate_regular = FixedIncome.perc_to_regular(rate)
        accrued_interest_perc = (rate_regular/frequency) * (accrued_days / total_days)
        return FixedIncome.regular_to_perc(accrued_interest_perc)

    @staticmethod
    def diff_month(date1, date2):
        print((date2.year - date1.year) * 12 + date2.month - date1.month)
        return (date2.year - date1.year) * 12 + date2.month - date1.month


bond_test = Bond(settlement=date(2020,7,15), maturity=date(2030,5,15), coupon_perc=0.625, 
                 price_perc=(100+0.5/32), frequency=2, basis=1)
bond_test._coupon_interval
bond_test._couppcd
bond_test._coupncd
bond_test._accrint
bond_test._dirty_price_perc
bond_test.price(0.62334818)
bond_test.get_yield()

Bond.accrint(issue=bond_test._couppcd, first_interest=bond_test._coupncd, settlement=bond_test._settlement, 
             rate=0.625, par=100, frequency=2, basis=1)




bond_test = Bond(date(2010,10,10), date(2016,1,7), 4.75, 1, 1)
bond_test._coupon_interval
bond_test._nperiod
bond_test._coupon_dates
bond_test._couppcd
bond_test._coupncd

