import QuantLib as ql
from typing import Dict
import json
from pathlib import Path
import matplotlib.pyplot as plt


# Get the current working directory
cwd = Path.cwd()
print(cwd)

class ArrCurve:
    def __init__(self, input_quotes: Dict[str, float], evaluation_date: ql.Date, 
                 overnight_index: ql.OvernightIndex = ql.Sofr()):
        self._curve_name = overnight_index.name().split("ON")[0]
        self._index = overnight_index
        self._eval_date = evaluation_date
        self._input_quotes_raw = input_quotes
        
        # Set Evaluation Date
        ql.Settings.instance().evaluationDate = self._eval_date
        
        # Get Conventions from json file
        conventions_file = cwd / "conventions" / "ArrCurveConventions.json"
        with open(conventions_file, "r") as file:
            conventions = json.load(file)
        self._conventions = conventions[self._curve_name.upper()]
        self.market = self._conventions["market"]
        
        try:
            self._rate_helpers: list[ql.OISRateHelper] = self.process_input_quotes_dict()
        except Exception as e:
            print(e)
            raise Exception("Error processing input quotes")
        
        # Create the curve
        self._calendar = self.get_calendar()
        self._day_counter = self.get_day_counter()
        self._curve = ql.PiecewiseLogCubicDiscount(0, self._calendar,
                                                   self._rate_helpers, self._day_counter)
        self._curve.enableExtrapolation()
    def get_calendar(self):
        if self.market == "US":
            return ql.UnitedStates(ql.UnitedStates.SOFR)
        elif self.market == "UK":
            return ql.UnitedKingdom(ql.UnitedKingdom.Settlement)
        elif self.market == "JP":
            return ql.Japan()
        elif self.market == "EU":
            return ql.TARGET()
        else:
            raise Exception(f"Can't find calendar for: {self.market}")
    
    def get_day_counter(self):
        if self.market == "US":
            return ql.Actual360()
        elif self.market == "UK":
            return ql.Actual365Fixed()
        elif self.market == "JP":
            return ql.Actual365Fixed()
        elif self.market == "EU":
            return ql.Actual360()
        else:
            raise Exception(f"Can't find day counter for: {self.market}")
    @property
    def eval_date(self):
        return self._eval_date
    
    @eval_date.setter
    def eval_date(self, date: ql.Date):  # noqa: F811
        self._eval_date = date
    
    def process_input_quotes_dict(self):
        rate_helpers = []
        for key, value in self._input_quotes_raw.items():
            tenor = ql.Period(key)
            rate = ql.QuoteHandle(ql.SimpleQuote(value/100))
            settlement_days = self._conventions["settlement_days"]
            ois_rate_helper = ql.OISRateHelper(settlement_days, tenor, rate, self._index) 
            rate_helpers.append(ois_rate_helper)
        return rate_helpers
    
    @property
    def curve(self):
        return self._curve
    
    def get_spot_rate(self, date: ql.Date):
        return self._curve.zeroRate(date, self._day_counter, ql.Continuous).rate()
    
    def get_discount_factor(self, date: ql.Date):
        return self._curve.discount(date)    
    
if __name__ == "__main__":
    eval_date = ql.Date(15, 1, 2025)
    input_quotes = {"1W": 1, "1M": 1.5, "3M": 2, "6M": 3, "1Y": 4 ,
                    "2Y": 4.5, "3Y": 4.6, "5Y": 4.7, "10Y": 5}
    arr_curve = ArrCurve(input_quotes, eval_date, ql.Sofr())
    # Plot the zero rates
    dates = [eval_date + ql.Period(i, ql.Months) for i in range(0, 360)]
    formatted_dates = [date.ISO() for date in dates]
    zero_rates = [arr_curve.get_spot_rate(date)*100 for date in dates]
    plt.plot(formatted_dates, zero_rates)
    plt.show()
    
    # # Set a new evaluation date
    # new_eval_date = ql.Date(15, 1, 2026)
    # arr_curve.eval_date = new_eval_date
    # # Plot the zero rates
    # dates = [new_eval_date + ql.Period(i, ql.Months) for i in range(0, 360)]
    # formatted_dates = [date.ISO() for date in dates]
    # zero_rates = [arr_curve.get_spot_rate(date)*100 for date in dates]
    # plt.plot(formatted_dates, zero_rates)
    # plt.show()
    
    