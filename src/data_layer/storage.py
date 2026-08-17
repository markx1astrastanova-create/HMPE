import os
import pandas as pd
import logging
from src.data_layer.provider import MarketDataProvider
from src.data_layer.validation import validate_ohlcv

logger = logging.getLogger(__name__)

class ParquetStorage:
    def __init__(self, base_dir: str = "data/raw/price"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_file_path(self, symbol: str) -> str:
        safe_symbol = symbol.replace("/", "_").replace("\\", "_")
        return os.path.join(self.base_dir, f"{safe_symbol}.parquet")

    def save_dataset(self, symbol: str, df: pd.DataFrame):
        if df.empty:
            logger.warning(f"Attempted to save empty dataset for {symbol}")
            return
        
        filepath = self._get_file_path(symbol)
        df.to_parquet(filepath, index=False)
        logger.info(f"Saved {len(df)} rows to {filepath}")

    def load_dataset(self, symbol: str) -> pd.DataFrame:
        filepath = self._get_file_path(symbol)
        if not os.path.exists(filepath):
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(filepath)
            return df
        except Exception as e:
            logger.error(f"Error reading parquet file for {symbol}: {e}")
            return pd.DataFrame()

    def get_latest_date(self, symbol: str) -> pd.Timestamp:
        df = self.load_dataset(symbol)
        if df.empty:
            return None
        return df['Date'].max()

def update_price_history(symbol: str, provider: MarketDataProvider, storage: ParquetStorage) -> pd.DataFrame:
    """
    Incrementally updates the historical price dataset for a symbol.
    """
    logger.info(f"Updating history for {symbol}")
    existing_df = storage.load_dataset(symbol)
    
    if existing_df.empty:
        logger.info(f"No existing data for {symbol}. Fetching full history.")
        new_df = provider.get_price_history(symbol)
        valid_df = validate_ohlcv(new_df, symbol)
        if not valid_df.empty:
            storage.save_dataset(symbol, valid_df)
        return valid_df

    latest_date = storage.get_latest_date(symbol)
    logger.info(f"Latest stored date for {symbol} is {latest_date.date() if latest_date else 'None'}")
    
    # We fetch a bit of overlapping data just in case of adjustments
    # e.g. start a few days before latest_date
    start_date = (latest_date - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
    
    new_data = provider.get_price_history(symbol, start=start_date)
    if new_data.empty:
        logger.info(f"No new data fetched for {symbol}")
        return existing_df

    # Merge and deduplicate
    combined = pd.concat([existing_df, new_data], ignore_index=True)
    valid_df = validate_ohlcv(combined, symbol)
    
    if len(valid_df) > len(existing_df) or valid_df['Date'].max() > latest_date:
        logger.info(f"Saving updated dataset for {symbol} ({len(valid_df)} rows total)")
        storage.save_dataset(symbol, valid_df)
    else:
        logger.info(f"No new actual records to append for {symbol}")
        
    return valid_df
