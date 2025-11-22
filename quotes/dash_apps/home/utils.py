from datetime import datetime, date
import pandas as pd

def timeframe_to_limit_date(time_frame: str) -> date:
    """
    From the button pressed (ex. 6m), return the associated start_date assuming the end_date is today.
    """
    match time_frame.lower():
        case "1m" | "3m" | "6m":
            nb_months = time_frame[0]
            start_datetime = datetime.today() - pd.tseries.offsets.DateOffset(months=int(nb_months))
            return start_datetime.date()

        case "ytd":
            return datetime(datetime.today().year, 1, 1).date()

        case "1y" | "3y":
            nb_years = time_frame[0]
            start_datetime = datetime.today() - pd.tseries.offsets.DateOffset(years=int(nb_years)) 
            return start_datetime.date()

        case "max":
            return date(2000, 1, 1)