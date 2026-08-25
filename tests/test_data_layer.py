import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from src.data_layer.validation import validate_ohlcv
from src.data_layer.storage import ParquetStorage, update_price_history
from src.data_layer.provider import MarketDataProvider
from src.api.main import get_price_history
from fastapi import HTTPException

# Mock Provider for testing without network
class MockProvider(MarketDataProvider):
    def __init__(self, data):
        self.data = data
    def get_price_history(self, symbol: str, start: str = None, end: str = None, interval: str = "1d") -> pd.DataFrame:
        if symbol not in self.data:
            return pd.DataFrame()
        df = self.data[symbol].copy()
        if start:
            df = df[df['Date'] >= pd.to_datetime(start)]
        if end:
            df = df[df['Date'] <= pd.to_datetime(end)]
        return df

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

def test_incremental_update_case_a(tmp_path):
    # Case A: new dates appended
    storage = ParquetStorage(base_dir=str(tmp_path))
    initial_data = pd.DataFrame({
        'Date': pd.to_datetime(['2026-08-10', '2026-08-11']),
        'Open': [100, 100], 'High': [110, 110], 'Low': [90, 90], 'Close': [105, 105], 'Volume': [100, 100]
    })
    storage.save_dataset("TEST", initial_data)
    
    new_data = pd.DataFrame({
        'Date': pd.to_datetime(['2026-08-11', '2026-08-12']),
        'Open': [100, 100], 'High': [110, 110], 'Low': [90, 90], 'Close': [105, 105], 'Volume': [100, 100]
    })
    provider = MockProvider({"TEST": pd.concat([initial_data, new_data]).drop_duplicates(subset=['Date'])})
    
    updated_df = update_price_history("TEST", provider, storage)
    assert len(updated_df) == 3
    assert list(updated_df['Date']) == list(pd.to_datetime(['2026-08-10', '2026-08-11', '2026-08-12']))
    
def test_incremental_update_case_b(tmp_path):
    # Case B: changed existing value
    storage = ParquetStorage(base_dir=str(tmp_path))
    initial_data = pd.DataFrame({
        'Date': pd.to_datetime(['2026-08-11']),
        'Open': [100], 'High': [110], 'Low': [90], 'Close': [105], 'Volume': [100]
    })
    storage.save_dataset("TEST", initial_data)
    
    new_data = pd.DataFrame({
        'Date': pd.to_datetime(['2026-08-11']),
        'Open': [100], 'High': [110], 'Low': [90], 'Close': [100], 'Volume': [100]
    })
    provider = MockProvider({"TEST": new_data})
    
    updated_df = update_price_history("TEST", provider, storage)
    assert len(updated_df) == 1
    assert updated_df.iloc[0]['Close'] == 100
    # verify it was actually saved
    loaded_df = storage.load_dataset("TEST")
    assert loaded_df.iloc[0]['Close'] == 100

def test_incremental_update_case_c(tmp_path):
    # Case C: identical data, no write
    storage = ParquetStorage(base_dir=str(tmp_path))
    initial_data = pd.DataFrame({
        'Date': pd.to_datetime(['2026-08-11']),
        'Open': [100], 'High': [110], 'Low': [90], 'Close': [105], 'Volume': [100]
    })
    storage.save_dataset("TEST", initial_data)
    
    provider = MockProvider({"TEST": initial_data})
    
    with patch.object(storage, 'save_dataset', wraps=storage.save_dataset) as spy:
        updated_df = update_price_history("TEST", provider, storage)
        assert len(updated_df) == 1
        spy.assert_not_called() # Should not save because nothing changed

def test_api_missing_values(tmp_path):
    # Test that NaN becomes null, not 0
    storage = ParquetStorage(base_dir=str(tmp_path))
    data = pd.DataFrame({
        'Date': pd.to_datetime(['2026-08-11']),
        'Open': [100.0], 'High': [110.0], 'Low': [90.0], 'Close': [np.nan], 'Volume': [100]
    })
    storage.save_dataset("TEST_API", data)
    
    with patch('src.api.main.storage', storage):
        resp = get_price_history("TEST_API", start=None, end=None)
        assert len(resp) == 1
        assert resp[0]['Close'] is None

def test_api_date_filtering(tmp_path):
    storage = ParquetStorage(base_dir=str(tmp_path))
    data = pd.DataFrame({
        'Date': pd.to_datetime(['2020-01-01', '2020-06-01', '2021-01-01']),
        'Open': [100.0, 105.0, 110.0], 'High': [110.0, 115.0, 120.0], 'Low': [90.0, 95.0, 100.0], 'Close': [105.0, 110.0, 115.0], 'Volume': [100, 100, 100]
    })
    storage.save_dataset("TEST_FILTER", data)
    with patch('src.api.main.storage', storage):
        # Filter with start and end
        resp = get_price_history("TEST_FILTER", start="2020-02-01", end="2020-12-31")
        assert len(resp) == 1
        assert resp[0]['Date'] == '2020-06-01'

def test_api_not_found():
    # Missing dataset should raise 404
    storage = ParquetStorage(base_dir="invalid_dir")
    with patch('src.api.main.storage', storage):
        with pytest.raises(HTTPException) as excinfo:
            get_price_history("NONEXISTENT", start=None, end=None)
        assert excinfo.value.status_code == 404
