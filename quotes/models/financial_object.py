"""
FinancialObject model - represents stocks, ETFs, indices, etc.
"""
from typing import Iterable, Optional
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
            created = FinancialData.objects.bulk_create(price_data, ignore_conflicts=True)
            logger.info(f"Saved {len(created)} new price records for {self.ticker} (skipped duplicates)")

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
            created = FinancialData.objects.bulk_create(div_data, ignore_conflicts=True)
            logger.info(f"Saved {len(created)} new dividend records for {self.ticker} (skipped duplicates)")


    def get_price_return(self, start_date: date, end_date: date | None = None) -> float | None:
        """
        Get Price Return between 2 dates
        """
        from .financial_data import FinancialData

        if end_date is None:
            end_date = datetime.today().date()

        ini_nav = FinancialData.objects.filter(
            id_object=self, 
            date__gte=start_date, 
            field="NAV", 
            origin="Yahoo Finance").order_by("date").values_list("value", flat=True).first()
        
        end_nav = FinancialData.objects.filter(
            id_object=self, 
            date__lte=end_date, 
            field="NAV", 
            origin="Yahoo Finance").order_by("-date").values_list("value", flat=True).first()

        if ini_nav is None or end_nav is None:
            return None
        
        return end_nav / ini_nav -1
    
    def get_div_return(self, start_date: date, end_date: date | None = None) -> float | None:
        """
        Get Dividend Return between 2 dates
        """
        from .financial_data import FinancialData

        if end_date is None:
            end_date = datetime.today().date()

        divs = FinancialData.objects.filter(
            id_object=self, 
            date__gte=start_date, 
            date__lte=end_date, 
            field="Dividends", 
            origin="Yahoo Finance").values_list("value", flat=True)

        total_divs = sum(divs)

        ini_nav = FinancialData.objects.filter(
            id_object=self, 
            date__gte=start_date, 
            field="NAV", 
            origin="Yahoo Finance").order_by("date").values_list("value", flat=True).first()
        
        if ini_nav is None:
            return None
        
        return total_divs / ini_nav
    
    def get_total_return(self, start_date: date, end_date: date | None = None) -> float | None:
        """
        Get Total Return between 2 dates
        """
        price_return = self.get_price_return(start_date, end_date)
        div_return = self.get_div_return(start_date, end_date)

        if price_return is None or div_return is None:
            return None
        
        return price_return + div_return