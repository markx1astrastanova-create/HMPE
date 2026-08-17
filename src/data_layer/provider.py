from abc import ABC, abstractmethod
import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class MarketDataProvider(ABC):
    @abstractmethod
    def get_price_history(self, symbol: str, start: str = None, end: str = None, interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical price data.
        If start and end are None, it should fetch the maximum available history.
        Returns a DataFrame with at least Date, Open, High, Low, Close, Volume.
        """
        pass

class YahooFinanceProvider(MarketDataProvider):
    def get_price_history(self, symbol: str, start: str = None, end: str = None, interval: str = "1d") -> pd.DataFrame:
        try:
            ticker = yf.Ticker(symbol)
            if start and end:
                df = ticker.history(start=start, end=end, interval=interval)
            elif start:
                df = ticker.history(start=start, interval=interval)
            else:
                df = ticker.history(period="max", interval=interval)

            if df.empty:
                logger.warning(f"No data returned for {symbol} from Yahoo Finance.")
                return pd.DataFrame()

            # yfinance returns DatetimeIndex, we need to reset it to make Date a column
            df = df.reset_index()
            
            # yfinance index might be named 'Date' or 'Datetime'
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            elif 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
                df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)

            # Ensure expected columns
            expected_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            for col in expected_columns:
                if col not in df.columns:
                    logger.error(f"Missing expected column {col} in data for {symbol}")
                    return pd.DataFrame()

            return df[expected_columns]

        except Exception as e:
            logger.error(f"Error fetching data for {symbol} from Yahoo Finance: {e}")
            return pd.DataFrame()
