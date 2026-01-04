from pandas.tseries.offsets import BDay
import pandas as pd
from datetime import date, datetime

def prev_business_day(given_date: date) -> date:
    return (pd.Timestamp(given_date) - BDay(1)).date()

def get_first_business_day_of_month(year: int, month: int) -> date:
    """
    Returns the first business day of a given month.
    """
    first_day = datetime(year, month, 1)
    first_business_day = first_day + BDay(0)  # Rolls to next business day if weekend
    return first_business_day.date()
