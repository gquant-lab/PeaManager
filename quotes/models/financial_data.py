"""
FinancialData model - stores time series data (prices, dividends, etc.)
"""
from django.db import models
from datetime import date

from .financial_object import FinancialObject


class FinancialData(models.Model):

    class TimeSeriesField(models.TextChoices):
        NAV = "NAV"
        Dividends = "Dividends"

    class DataOrigin(models.TextChoices):
        YF = "Yahoo Finance"
        PROVIDER = "Provider"
        FT = "Financial Times"

    class Meta:
        ordering = ["-date"]
        unique_together = [('id_object', 'date', 'field')]

    id_object = models.ForeignKey(FinancialObject, on_delete=models.CASCADE)
    date = models.DateField()
    field = models.CharField(max_length=15, choices=TimeSeriesField.choices)
    value = models.FloatField(default=0)
    origin = models.CharField(max_length=20, choices = DataOrigin.choices)

    def __str__(self):
        return f"object: {self.id_object}, date: {self.date}, value: {self.value}"
    
    @staticmethod          
    def get_price_most_recent_date() -> date:
        """
        Get the second most recent date from price dates, in case all values were not updated to the most recent one
        """
        dates = sorted(FinancialData.objects.values_list("date", flat=True).distinct(), reverse=True)
        return dates[1] if len(dates) > 1 else dates[0]
