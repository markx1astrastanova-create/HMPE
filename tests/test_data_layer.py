import pytest
import pandas as pd
import numpy as np
from src.data_layer.validation import validate_ohlcv

def test_validate_ohlcv_empty():
    df = pd.DataFrame()
    valid_df = validate_ohlcv(df, "TEST")
    assert valid_df.empty

def test_validate_ohlcv_missing_columns():
    df = pd.DataFrame({'Date': ['2023-01-01'], 'Open': [100]})
    valid_df = validate_ohlcv(df, "TEST")
    assert valid_df.empty

def test_validate_ohlcv_valid():
    data = {
        'Date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'Open': [100.0, 105.0],
        'High': [110.0, 115.0],
        'Low': [95.0, 100.0],
        'Close': [105.0, 110.0],
        'Volume': [1000, 1500]
    }
    df = pd.DataFrame(data)
    valid_df = validate_ohlcv(df, "TEST")
    assert len(valid_df) == 2
    assert list(valid_df['Date']) == data['Date'].tolist()

def test_validate_ohlcv_invalid_prices():
    data = {
        'Date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'Open': [100.0, 105.0],
        'High': [90.0, 115.0], # Invalid High < Open
        'Low': [95.0, 100.0],
        'Close': [105.0, 110.0],
        'Volume': [1000, 1500]
    }
    df = pd.DataFrame(data)
    valid_df = validate_ohlcv(df, "TEST")
    assert len(valid_df) == 1
    assert valid_df.iloc[0]['Open'] == 105.0

def test_validate_ohlcv_duplicates():
    data = {
        'Date': pd.to_datetime(['2023-01-01', '2023-01-01']),
        'Open': [100.0, 105.0],
        'High': [110.0, 115.0],
        'Low': [95.0, 100.0],
        'Close': [105.0, 110.0],
        'Volume': [1000, 1500]
    }
    df = pd.DataFrame(data)
    valid_df = validate_ohlcv(df, "TEST")
    assert len(valid_df) == 1
    assert valid_df.iloc[0]['Close'] == 110.0 # keep='last'

def test_validate_ohlcv_nan_values():
    data = {
        'Date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'Open': [100.0, np.nan],
        'High': [110.0, 115.0],
        'Low': [95.0, 100.0],
        'Close': [105.0, 110.0],
        'Volume': [1000, 1500]
    }
    df = pd.DataFrame(data)
    valid_df = validate_ohlcv(df, "TEST")
    assert len(valid_df) == 1
    assert valid_df.iloc[0]['Open'] == 100.0
