import yfinance as yf
import logging
from typing import Optional
from datetime import date, datetime, time

from .base import SourceType, DataSource, DataSourceResult

logger = logging.getLogger(__name__)

class YahooDataSource(DataSource):
    """
    Yahoo Finance data source implementation.
    """
    def get_source_name(self) -> str:
        return SourceType.YAHOO_FINANCE
    
    def _fetch_and_parse(self, ticker: str, **history_kwargs) -> Optional[DataSourceResult]:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(**history_kwargs)

            if df.shape[0] == 0:
                logger.warning(f"No data returned from Yahoo Finance for ticker {ticker}")
                return None
            
            # Extract prices and dividends
            prices = list(df["Close"].items())
            divs = list(df["Dividends"][df["Dividends"] != 0].items())

            # Convert to (date, value) tuples
            prices = [(i.date(), float(price)) for i, price in prices]
            dividends = [(i.date(), float(div)) for i, div in divs]
            
            logger.info(f"Successfully fetched {len(prices)} prices and {len(dividends)} dividends for {ticker}")
            
            return DataSourceResult(prices, dividends, self.get_source_name())
        
        
        except Exception as e:
            logger.error(f"Error fetching from Yahoo Finance for ticker {ticker}: {e}", exc_info=True)
            return None

    def fetch_historical_data(self, ticker: str) -> Optional[DataSourceResult]:
        logger.debug(f"Fetching historical data for {ticker}")
        return self._fetch_and_parse(ticker=ticker, period="max")
        
    def fetch_incremental_data(self, ticker: str, since_date: date) -> Optional[DataSourceResult]:
        logger.debug(f"Fetching incremental data for {ticker} since {since_date}")
        result = self._fetch_and_parse(
            ticker, 
            start=datetime.combine(since_date, time.min),
            end=datetime.now()
        )
        
        if result:
            # Filter out the since_date itself
            result.prices = [(d, v) for d, v in result.prices if d != since_date]
            result.dividends = [(d, v) for d, v in result.dividends if d != since_date]
        
        return result