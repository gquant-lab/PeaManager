from abc import ABC, abstractmethod
from datetime import date
from typing import List, Tuple, Optional
from enum import Enum

class SourceType(Enum):
    YAHOO_FINANCE = "Yahoo Finance"
    FMP = "Financial Modeling Prep"
    CUSTOM_PROVIDER = "Custom Provider"

class DataSourceResult:
    """
    Container for data fetched from a source
    """

    def __init__(self, prices: List[Tuple[date, float]], dividends: List[Tuple[date, float]], source_name: str):
        self.prices = prices
        self.dividends = dividends
        self.source_name = source_name

class DataSource(ABC):
    """
    Abstract base class for data sources
    """

    @abstractmethod
    def fetch_historical_data(self, ticker: str) -> Optional[DataSourceResult]:
        """Fetch all historical data for a ticker"""
        pass

    @abstractmethod
    def fetch_incremental_data(self, ticker: str, since_date: date) -> Optional[DataSourceResult]:
        """Fetch data since a specific date"""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this data source"""
        pass