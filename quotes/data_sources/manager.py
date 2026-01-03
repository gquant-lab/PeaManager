import logging
import time
from typing import List, Optional
from datetime import date
from .base import DataSource, DataSourceResult
from .yahoo import YahooDataSource

logger = logging.getLogger(__name__)

class DataSourceManager:
    """
    Manages multiple data sources with fallback logic.
    Tries sources in order until one succeeds.
    """
    
    def __init__(self, sources: Optional[List[DataSource]] = None):
        """
        Initialize with a list of data sources.
        If none provided, defaults to [YahooDataSource]
        """
        if sources is None:
            self.sources = [YahooDataSource()]
        else:
            self.sources = sources
        
        logger.info(f"DataSourceManager initialized with sources: {[s.get_source_name().value for s in self.sources]}")

    def _try_sources(self, method_name: str, ticker: str, **kwargs) -> Optional[DataSourceResult]:
        """
        Generic method to try a fetch operation across all sources.
        
        Args:
            method_name: Name of the method to call on each source (e.g., 'fetch_historical_data')
            ticker: The ticker symbol
            **kwargs: Additional arguments to pass to the source method
        """
        logger.info(f"Attempting {method_name} for {ticker}")
        
        for source in self.sources:
            start_time = time.time()
            source_name = source.get_source_name().value
            
            logger.debug(f"Trying {source_name} for {ticker}")
            
            # Call the method dynamically
            method = getattr(source, method_name)
            result = method(ticker, **kwargs)
            
            duration = time.time() - start_time
            
            if result:
                logger.info(f"✓ Successfully fetched data for {ticker} from {source_name} in {duration:.2f}s")
                return result
            else:
                logger.warning(f"✗ Failed to fetch data for {ticker} from {source_name} (took {duration:.2f}s)")
        
        logger.error(f"All data sources failed for {ticker} ({method_name})")
        return None
    
    def fetch_historical_data(self, ticker: str) -> Optional[DataSourceResult]:
        """Try to fetch historical data from available sources."""
        return self._try_sources('fetch_historical_data', ticker)
    
    def fetch_incremental_data(self, ticker: str, since_date: date) -> Optional[DataSourceResult]:
        """Try to fetch incremental data from available sources."""
        return self._try_sources('fetch_incremental_data', ticker, since_date=since_date)
    

