"""
FinancialObject model - represents stocks, ETFs, indices, etc.
"""
from typing import Iterable
from django.db import models
import yfinance as yf
from datetime import date, datetime, time
import warnings
warnings.filterwarnings("error")


class FinancialObject(models.Model):
    
    class ObjectType(models.TextChoices):
        STOCK = "Stock"
        INDEX = "Index"
        ETF = "ETF"
        ETFShare = "ETFShare"

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=ObjectType.choices)
    isin = models.CharField(max_length=12)
    ticker = models.CharField(max_length=12, blank=True, null=True)

    def __str__(self):
        return f"{self.category} - {self.name}"

    def get_latest_available_nav(self):
        """
        Queries FinancialData table to see until when data has been populated.
        """
        from .financial_data import FinancialData
        
        if (FinancialData.objects.filter(id_object=self.id).exists()):
            return FinancialData.objects.filter(id_object=self.id).order_by("-date").first().date
        else:
            return None

    def update_nav_and_divs(self):
        """
        Updates time series
        """
        from .financial_data import FinancialData

        stock = yf.Ticker(self.ticker)
        data = []

        if self.get_latest_available_nav() == None:
            # Take everything from YF
            
            df = stock.history(period="max")
            prices: Iterable[tuple, float] = df["Close"].items() #type: ignore
            divs: Iterable[tuple, float] = df["Dividends"][df["Dividends"] != 0].items() #type: ignore

            for i, price in prices:
                new = FinancialData(id_object=self, date=i.date(), field="NAV", value=price, origin="Yahoo Finance")
                data.append(new)
            FinancialData.objects.bulk_create(data)
            
            data = []
            for i, div in divs:
                new = FinancialData(id_object=self, date=i.date(), field="Dividends", value=div, origin="Yahoo Finance")
                data.append(new)
            FinancialData.objects.bulk_create(data)

        else:
            last_date = self.get_latest_available_nav()
            if self.isin == "LU1834983477":
                  last_date = date(2022,1,19)
            df = stock.history(start=datetime.combine(last_date, time.min),
                               end=datetime.now())

            if df.shape[0] == 0:
                # No data
                print(f"No data for {self.ticker}!")
                return 
            
            prices = list(df["Close"].items()) #type: ignore
            divs = list(df["Dividends"][df["Dividends"] != 0].items()) #type: ignore

            for i,price in prices:
                if i.date() == last_date:
                    continue
                new = FinancialData(id_object=self, date=i.date(), field="NAV", value=price, origin="Yahoo Finance")
                data.append(new)

            FinancialData.objects.bulk_create(data)

            data = []
            for i, div in divs:
                if i.date() == last_date:
                    continue
                new = FinancialData(id_object=self, date=i.date(), field="Dividends", value=div, origin="Yahoo Finance")
                data.append(new)
            FinancialData.objects.bulk_create(data)

    def get_perf(self, start_date, end_date=datetime.today().date()):
        """
        Get Return between 2 dates
        """
        from .financial_data import FinancialData

        ini_nav = FinancialData.objects.filter(id_object=self, date=start_date, field="NAV", origin="Yahoo Finance").values_list("value", flat=True)
        end_nav = FinancialData.objects.filter(id_object=self, date=end_date, field="NAV", origin="Yahoo Finance").values_list("value", flat=True)
        
        ini_nav = list(ini_nav)[0]
        end_nav = list(end_nav)[0]

        return end_nav / ini_nav -1
