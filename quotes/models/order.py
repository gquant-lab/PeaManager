"""
Order model - represents buy/sell transactions.
"""
from django.db import models

from .portfolio import Portfolio
from .financial_object import FinancialObject


class Order(models.Model):

    class OrderDirection(models.TextChoices):
        BUY = "BUY"
        SELL = "SELL"

    date = models.DateField()
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="orders")
    id_object = models.ForeignKey(FinancialObject, on_delete=models.CASCADE)
    direction = models.CharField(max_length=4, choices=OrderDirection.choices)
    nb_items = models.IntegerField(default=1)
    price = models.FloatField(default=100)
    total_fee = models.FloatField(default=0)

    def __str__(self):
        return f"{self.portfolio.owner} | {self.date} | {self.id_object.name} ({self.nb_items})"
