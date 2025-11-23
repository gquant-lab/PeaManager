"""
YahooFinanceQuery - utility class for querying Yahoo Finance data.
"""
from datetime import date
import pandas as pd

from .financial_object import FinancialObject
from .financial_data import FinancialData


class YahooFinanceQuery:

    @staticmethod
    def get_prices_from_inventory(fin_objs: list[FinancialObject], from_date: date, until_date: date) -> pd.DataFrame:
        """
        Queries the database for prices, and returns dataframe (objs x dates)
        """
        if not all(isinstance(x, FinancialObject) for x in fin_objs):
              raise TypeError(f"Not a list of Financial Objects:{type(fin_objs[0])}")
        
        def query_price_from_db(obj: FinancialObject, from_date: date, until_date: date) -> pd.DataFrame:
            """
            Query the database for prices of a single financial object
            """
            df = pd.DataFrame(list(
                FinancialData.objects.filter(id_object=obj.id, field="NAV", date__gte=from_date, date__lte=until_date)
                .values("date", "value")))
            
            if df.empty:
                  raise ValueError(f"No data for {obj.name} (ISIN is {obj.isin}) between "
                                   f"{from_date} and {until_date}.")
            
            df = df.set_index("date").squeeze().rename(obj.name)
            return df

        # Query prices and adjust dfs to series with date index and relevant column names 
        dfs = [query_price_from_db(obj, from_date, until_date) for obj in fin_objs]
        prices = dfs[0].to_frame() if len(dfs) == 1 else pd.concat(dfs, axis=1, sort=True)

        # For some reason, datetime index unordered (later dates before earlier dates)
        # => messes up return calculation
        prices.sort_index(inplace=True)

        return prices
    
    @staticmethod
    def get_divs_from_inventory(fin_objs: list[FinancialObject], from_date: str, until_date: str) -> pd.DataFrame:

        if not all(isinstance(x, FinancialObject) for x in fin_objs):
              raise TypeError(f"Not a list of Financial Objects:{type(fin_objs[0])}")
        
        # Query prices
        dfs = [pd.DataFrame(list(
                FinancialData.objects.filter(
                      id_object=obj.id, field=FinancialData.TimeSeriesField.Dividends, origin="Yahoo Finance", date__gte=from_date, date__lte=until_date)
                .values("date", "value"))) for obj in fin_objs]

        # ISSUE IS HERE => PUT 0 WHEN NO DIVIDEND WAS PROVIDED
        # Adjust dfs to series with date index and relevant column names 
        for i, df in enumerate(dfs):
            if not df.empty:
                df = df.set_index("date")
                df = pd.Series(data=df.squeeze(), index=df.index, name=fin_objs[i].name) if df.shape == (1,1) else\
                     df.squeeze().rename(fin_objs[i].name)
            else:
                df = pd.Series(name=fin_objs[i].name)

            dfs[i] = df
        
        # To dataframe with ordered index dates
        divs = dfs[0].to_frame() if len(dfs) == 1 else pd.concat(dfs, axis=1, sort=True)
        divs.fillna(0, inplace=True)

        return divs
