"""
Models package for the quotes application.

This package contains all Django models organized by domain:
- financial_object: FinancialObject (stocks, ETFs, indices)
- account: AccountOwner
- portfolio: Portfolio, PortfolioEntry, PortfolioInventory
- order: Order
- financial_data: FinancialData (time series data)
- yahoo_finance: YahooFinanceQuery (utility class)
"""
import django_stubs_ext
django_stubs_ext.monkeypatch()

from .financial_object import FinancialObject
from .account import AccountOwner
from .portfolio import Portfolio, PortfolioEntry, PortfolioInventory
from .order import Order
from .financial_data import FinancialData
from .yahoo_finance import YahooFinanceQuery

__all__ = [
    'FinancialObject',
    'AccountOwner',
    'Portfolio',
    'PortfolioEntry',
    'PortfolioInventory',
    'Order',
    'FinancialData',
    'YahooFinanceQuery',
]
