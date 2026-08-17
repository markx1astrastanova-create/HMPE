import pandas as pd
import logging

logger = logging.getLogger(__name__)

def validate_ohlcv(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Validates and cleans OHLCV data.
    """
    if df is None or df.empty:
        logger.warning(f"Empty dataset received for {symbol}")
        return pd.DataFrame()

    required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns for {symbol}: {missing_cols}")
        return pd.DataFrame()

    # Ensure numeric types
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with NaN in critical columns
    before_len = len(df)
    df = df.dropna(subset=['Date', 'Open', 'High', 'Low', 'Close'])
    after_len = len(df)
    if before_len != after_len:
        logger.info(f"Dropped {before_len - after_len} rows with NaN values for {symbol}")

    if df.empty:
        return df

    # Basic validations
    invalid_mask = (
        (df['High'] < df['Low']) |
        (df['High'] < df['Open']) |
        (df['High'] < df['Close']) |
        (df['Low'] > df['Open']) |
        (df['Low'] > df['Close']) |
        (df['Open'] < 0) |
        (df['High'] < 0) |
        (df['Low'] < 0) |
        (df['Close'] < 0)
    )

    invalid_count = invalid_mask.sum()
    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} invalid OHLC rows for {symbol}. Dropping them.")
        df = df[~invalid_mask]

    # Deduplicate by Date
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['Date'], keep='last')
    after_dedup = len(df)
    if before_dedup != after_dedup:
        logger.info(f"Dropped {before_dedup - after_dedup} duplicate dates for {symbol}")

    # Sort chronologically
    df = df.sort_values(by='Date', ascending=True).reset_index(drop=True)

    return df
