"""
FinancialObject model - represents stocks, ETFs, indices, etc.
"""
from typing import Iterable
from django.db import models
from datetime import date, datetime, time
import logging

logger = logging.getLogger(__name__)

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
        from quotes.data_sources.manager import DataSourceManager

        manager = DataSourceManager()
        last_date = self.get_latest_available_nav()

        # Handle special case for specific ISIN
        if self.isin == "LU1834983477" and last_date:
            last_date = date(2022,1,19)

        if last_date is None:
            logger.info(f"Fetching historical data for {self.ticker}")
            result = manager.fetch_historical_data(self.ticker)
        else:
            logger.info(f"Fetching incremental data for {self.ticker} since {last_date}")
            result = manager.fetch_incremental_data(self.ticker, last_date)

        if not result:
            logger.warning(f"No data fetched for {self.ticker}")
            return
        
        # Save prices to database
        price_data = []
        for date_val, price_val in result.prices:
            price_data.append(FinancialData(
                id_object=self,
                date=date_val,
                field="NAV",
                value=price_val,
                origin=result.source_name.value
            ))

        if price_data:
            FinancialData.objects.bulk_create(price_data)
            logger.info(f"Saved {len(price_data)} price records for {self.ticker}")

        # Save dividends to database
        div_data = []
        for date_val, div_val in result.dividends:
            div_data.append(
                FinancialData(
                    id_object=self,
                    date=date_val,
                    field="Dividends",
                    value=div_val,
                    origin=result.source_name.value
                )
            )
        
        if div_data:
            FinancialData.objects.bulk_create(div_data)
            logger.info(f"Saved {len(div_data)} dividends for {self.ticker}")


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
