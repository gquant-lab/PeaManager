from pandas.tseries.offsets import BDay
from datetime import date

def prev_business_day(given_date: date) -> date:
    return given_date - BDay(1)
