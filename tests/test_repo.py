import unittest
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
import math
import sys
from scipy.optimize import root
sys.path.append("fincomepy")  ## TO DO: change this
from fincomepy import Repo

class Test(unittest.TestCase):

    def test_return_values(self):
        repo_test = Repo(settlement=date(2020,7,15), maturity=date(2030,5,15), coupon_perc=0.625, 
            price_perc=(99+30/32), frequency=2, basis=1, 
            bond_face_value=100000000, repo_period=1, repo_rate_perc=0.145)
        self.assertTrue(abs(repo_test._perc_dict["accrint"] - 0.1036) < 0.0001)
        self.assertTrue(abs(repo_test._perc_dict["repo_rate"] - 0.145) < 1e-6)
        self.assertTrue(abs(repo_test.start_payment() - 100041100.54) < 0.01)
        self.assertTrue(abs(repo_test.end_payment() - 100041503.49) < 0.01)

        repo_test = Repo(settlement=date(2020,7,16), maturity=date(2030,5,15), coupon_perc=0.625, 
            price_perc=99.953125, frequency=2, basis=1, 
            bond_face_value=100000000, repo_period=32, repo_rate_perc=0.145)
        self.assertTrue(abs(repo_test._perc_dict["accrint"] - 0.1053) < 0.0001)
        self.assertTrue(abs(repo_test.start_payment() - 100058423.91) < 0.01)
        self.assertTrue(abs(repo_test.end_payment() - 100071320.33) < 0.01)
        self.assertTrue(abs(repo_test.break_even() - 0.6343) < 0.01)
        

if __name__ == '__main__':
    unittest.main()


