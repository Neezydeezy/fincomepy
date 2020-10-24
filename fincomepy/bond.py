from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
import math
from scipy.optimize import root
from fincomepy.fixedincome import FixedIncome

class Bond(FixedIncome):
    '''
    A class used to perform bond related calculations.

    Attributes
    ----------
    _reg_dict : dict
        A dictionary which contains the regular quantities. The keys of _reg_dict should be the
        same as that of _perc_dict.
    _perc_dict : dict
        A dictionary which contains the quantities in percent. The keys of _perc_dict should be the
        same as that of _reg_dict.
    _settlement: datetime.date
        A date object which specifies the bond settlement date.
    _maturity: datetime.date
        A date object which specifies the maturity date.
    _frequency: int
        An integer which specifies coupon payment frequency.
    _basis: int
        An integer which indicates day count convention. 
    _redemption: float
        A float which specifies bond redemption (in percent). 
    _couppcd: datetime.date
        A date object which indicates the previous coupon payment date.
    _coupncd: datetime.date
        A date object which indicates the next coupon payment date.
    _yld: float
        A float which indicates bond yield (in percent).
    _mac_duration: float
        A float which indicates the Macaulay duration of a bond.
    _mod_duration: float
        A float which indicates the modified duration of a bond.
    _DV01: float
        A float which indicates the DV01 of a bond.
    _convexity: float
        A float which indicates the convexity of a bond.
    
    Methods
    -------
    couppcd(settlement, maturity, frequency, basis)
        Get the previous coupon payment date.
    coupncd(settlement, maturity, frequency, basis)
        Get the next coupon payment date.
    accrint(issue, first_interest, settlement, rate, par, frequency, basis)
        Calculate the accrued interest of coupon.
    '''

    def __init__(self, settlement, maturity, coupon_perc, price_perc, frequency, basis=1, redemption=100, yld=None):
        
        '''
        0: 30/360
        1: actual/actual
        2: actual/360
        3: actual/365
        4: 30E/360
    
        '''
        
        super().__init__()
        self._settlement = settlement
        self._maturity = maturity
        self._perc_dict["coupon"] = coupon_perc
        self._perc_dict["clean_price"] = self.parse_price(price_perc)
        self._frequency = frequency
        self._basis = basis
        self._redemption = redemption
        self._couppcd = Bond.couppcd(settlement, maturity, frequency, basis)
        self._coupncd = Bond.coupncd(settlement, maturity, frequency, basis)
        self._perc_dict["accrint"] = Bond.accrint(issue=self._couppcd, first_interest=self._coupncd, settlement=self._settlement,
            rate=self._perc_dict["coupon"], par=1, frequency=self._frequency, basis=self._basis)
        self._perc_dict["dirty_price"] = self._perc_dict["clean_price"] + self._perc_dict["accrint"]
        self.update_dict()
        self._yld = yld   ## TO DO: check if yld can be put into perc_dict
        self._mac_duration = None
        self._mod_duration = None
        self._DV01 = None
        self._convexity = None
    
    @staticmethod
    def couppcd(settlement, maturity, frequency, basis):
        coupon_interval = 12 / frequency
        nperiod = math.ceil((Bond.diff_month(settlement, maturity))/coupon_interval)
        pcd = maturity - relativedelta(months=coupon_interval) * nperiod
        if maturity==Bond.last_day_in_month(maturity):
            return Bond.last_day_in_month(pcd)
        return pcd
    
    @staticmethod
    def coupncd(settlement, maturity, frequency, basis):
        coupon_interval = 12 / frequency
        nperiod = math.ceil((Bond.diff_month(settlement, maturity))/coupon_interval)
        ncd = maturity - relativedelta(months=coupon_interval) * (nperiod - 1)
        if maturity==Bond.last_day_in_month(maturity):
            return Bond.last_day_in_month(ncd)
        return ncd
    
    @staticmethod
    def accrint(issue, first_interest, settlement, rate, par=1, frequency=2, basis=1):
        if issue > first_interest:
            raise Exception('issue date cannot be later than first interest date.')
        if basis == 2:
            return (settlement - issue).days / 360 * rate
        if basis == 3:
            return (settlement - issue).days / 365 * rate
        total_days = Bond.day_count(issue, first_interest, basis)
        accrued_days = Bond.day_count(issue, settlement, basis)
        accrued_interest = (rate / frequency) * (accrued_days / total_days)
        return accrued_interest * par
    
    @staticmethod
    def day_count(date1, date2, basis):
        if basis == 0:
            Y1, M1, D1 = date1.year, date1.month, date1.day
            Y2, M2, D2 = date2.year, date2.month, date2.day
            if date1 == Bond.last_day_in_month(date1) and date2 == Bond.last_day_in_month(date2) \
                and date1.month == 2 and date2.month == 2:
                D2 = 30
            if date1 == Bond.last_day_in_month(date1) and date1.month == 2:
                D1 = 30
            if D2 == 31 and (D1 == 30 or D1 == 31):
                D2 = 30
            if D1 == 31:
                D1 = 30
            return 360 * (Y2 - Y1) + 30 * (M2 - M1) + (D2 - D1)
        if basis == 4:
            if date1.day == 31:
                date1 = date1 - relativedelta(days=1)
            if date2.day == 31:
                date2 = date2 - relativedelta(days=1)
            return 360 * (date2.year - date1.year) + 30 * (date2.month - date1.month) + (date2.day - date1.day)
        return (date2 - date1).days

    @staticmethod
    def dirty_price(settlement, maturity, rate, yld, redemption, frequency, basis):
        pcd = Bond.couppcd(settlement, maturity, frequency, basis)
        ncd = Bond.coupncd(settlement, maturity, frequency, basis)
        first_period = (ncd - settlement).days / (ncd - pcd).days
        coupon_interval = 12 / frequency  
        nperiod = math.ceil((Bond.diff_month(settlement, maturity)) / coupon_interval)  
        periods = np.array([first_period + i for i in range(nperiod)])
        CF_perc = np.array([rate / frequency] * nperiod)
        CF_perc[-1] += redemption 
        CF_regular = CF_perc * 0.01
        yld_regular = yld * 0.01
        DF = 1 / (1 + yld_regular / frequency) ** periods
        CF_PV = CF_regular * DF
        CF_PV_total = sum(CF_PV)
        return CF_PV_total * 100  

    @staticmethod
    def yld(settlement, maturity, rate, pr, redemption, frequency, basis, *args, **kwargs):
        pcd = Bond.couppcd(settlement, maturity, frequency, basis)
        ncd = Bond.coupncd(settlement, maturity, frequency, basis)
        accrued_interest = Bond.accrint(issue=pcd, first_interest=ncd, settlement=settlement, rate=rate, par=1, frequency=frequency, basis=basis)
        dirty_price_target = accrued_interest + pr
        sol = root(lambda x: Bond.dirty_price(settlement, maturity, rate, x, redemption, frequency, basis) - dirty_price_target, 
            [0.01], *args, **kwargs)
        yld = sol.x[0]
        assert yld >= 0 and yld <= 100
        return yld

    def intermediate_values(self):
        coupon_interval = 12 / self._frequency  
        nperiod = math.ceil((Bond.diff_month(self._settlement, self._maturity))/coupon_interval) 
        first_period = (self._coupncd - self._settlement).days / (self._coupncd - self._couppcd).days
        periods = np.array([first_period + i for i in range(nperiod)])
        CF_perc = np.array([self._perc_dict["coupon"] / self._frequency] * nperiod)
        CF_perc[-1] += self._redemption
        CF_regular = CF_perc*0.01
        if self._yld is None:
            self._yld = self.yld(self._settlement, self._maturity, self._perc_dict["coupon"], self._perc_dict["clean_price"],
                                 self._redemption, self._frequency, self._basis)
        yield_regular = self._yld * 0.01
        DF = 1 / (1 + yield_regular / self._frequency) ** periods
        return (periods, CF_regular, DF)
    
    def mac_duration(self):
        if self._mac_duration:
            return self._mac_duration
        periods, CF_regular, DF = self.intermediate_values()
        CF_PV = CF_regular * DF
        CF_PV_times_p = CF_PV * periods
        self._mac_duration = CF_PV_times_p.sum() / self._reg_dict["dirty_price"] / self._frequency
        return self._mac_duration

    def mod_duration(self, yld_change_perc=0.01):
        if self._mod_duration:
            return self._mod_duration
        if self._yld is None:
            original_yield_perc = self.yld(self._settlement, self._maturity, self._perc_dict["coupon"], self._perc_dict["clean_price"],
                                           self._redemption, self._frequency, self._basis)
        else:
            original_yield_perc = self._yld
        yield_up_perc = original_yield_perc + yld_change_perc
        yield_down_perc = original_yield_perc - yld_change_perc
        dirty_price_up_perc = self.dirty_price(self._settlement, self._maturity, self._perc_dict["coupon"], yield_up_perc,
                                               self._redemption, self._frequency, self._basis)  
        dirty_price_down_perc = self.dirty_price(self._settlement, self._maturity, self._perc_dict["coupon"], yield_down_perc,
                                               self._redemption, self._frequency, self._basis) 
        price_change_up_perc = dirty_price_up_perc - self._perc_dict["dirty_price"]
        price_change_down_perc = dirty_price_down_perc - self._perc_dict["dirty_price"]
        relative_change_up = price_change_up_perc / self._perc_dict["dirty_price"]
        relative_change_down = price_change_down_perc / self._perc_dict["dirty_price"]
        self._mod_duration = (abs(relative_change_up) + abs(relative_change_down)) / 2 / (yld_change_perc * 0.01) 
        return self._mod_duration
    
    def DV01(self):
        if self._DV01:
            return self._DV01
        if self._mod_duration is None:
            self.mod_duration()
        self._DV01 = self._mod_duration * self._reg_dict["dirty_price"]
        return self._DV01
    
    def convexity(self):
        if self._convexity:
            return self._convexity
        periods, CF_regular, DF = self.intermediate_values()
        CF_PV = CF_regular * DF
        CF_PV_times_p = CF_PV * periods
        CF_PV_times_p_2 = CF_PV * periods * periods
        all = (CF_PV_times_p + CF_PV_times_p_2) / self._reg_dict["dirty_price"]
        if self._yld is None:
            self._yld = self.yld(self._settlement, self._maturity, self._perc_dict["coupon"], self._perc_dict["clean_price"],
                                 self._redemption, self._frequency, self._basis)
        yield_regular = self._yld * 0.01
        self._convexity = all.sum() / (4 * (1 + yield_regular / self._frequency) ** 2)
        return self._convexity
    
    def price_change(self, yld_change_perc):
        DV01 = self.DV01()
        convexity = self.convexity()
        yld_change_reg = yld_change_perc * 0.01
        price_change_reg = (-1) * DV01 * yld_change_reg + self._reg_dict["dirty_price"] * convexity / 2 * (yld_change_reg ** 2)
        return price_change_reg * 100
            
    @staticmethod
    def diff_month(date1, date2):
        return (date2.year - date1.year) * 12 + date2.month - date1.month
    
    @staticmethod
    def last_day_in_month(original_date):
        next_month = original_date.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    @staticmethod
    def parse_price(pr):
        if not isinstance(pr, (int, float, str)):
            raise Exception('price should be int, float, or str.')
        if isinstance(pr, (int, float)):
            return pr
        quotelist = pr.split('-')
        assert len(quotelist) <= 2
        quotelist = [item.strip() for item in quotelist]
        if len(quotelist) == 1:
            return int(quotelist[0])
        firstnum = quotelist[0]
        secondnum = quotelist[1]
        if secondnum.endswith('+'):
            return int(firstnum) + (int(secondnum[:-1]) + 0.5) / 32
        return int(firstnum) + int(secondnum) / 32

    def coupon_dates(self):
        coupon_interval = 12 / self._frequency
        periods = math.floor((self.diff_month(self._settlement, self._maturity)) / coupon_interval)
        coupon_dates = [self._maturity - relativedelta(months=coupon_interval) * i for i in range(periods + 1)]
        if self._maturity==Bond.last_day_in_month(self._maturity):
            coupon_dates = [Bond.last_day_in_month(item) for item in coupon_dates]
        return coupon_dates


