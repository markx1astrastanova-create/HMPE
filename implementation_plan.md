# Historical Market Engine (HMPE) - Initial Backend Data Architecture

We are building the Historical Market Engine (HMPE) from scratch in the new `HMPE` directory (`x:\Python Project\HMPE`). The goal is to establish a robust backend data layer that leverages `yfinance`, fetches the maximum available history for symbols, and caches the dataset locally using Parquet files. This dataset will serve as the foundational source of truth for the entire application.

## User Review Required

> [!WARNING]
> Since the `HMPE` folder is currently empty, we will initialize a new Python project structure here. We will set up a FastAPI backend (to serve the API for a future frontend) and implement the complete Data Provider, Validation, and Storage layers as requested.

## Proposed Changes

---

### Backend Setup

We will create a new Python environment/project structure inside `x:\Python Project\HMPE`.

#### [NEW] `requirements.txt`
Dependencies:
- `fastapi`
- `uvicorn`
- `pandas`
- `numpy`
- `yfinance`
- `pyarrow` (for Parquet storage)
- `pytest`

#### [NEW] `src/data_layer/provider.py`
Abstracts the market data provider.
- `MarketDataProvider` (Abstract Base Class)
- `YahooFinanceProvider` (Implementation using `yfinance`)
- Supports fetching full history.

#### [NEW] `src/data_layer/validation.py`
Validates the fetched data.
- Ensures OHLC columns exist.
- Checks numeric validity (High >= Low, no negative prices).
- Deduplicates and sorts by date ascending.

#### [NEW] `src/data_layer/storage.py`
Handles local Parquet storage and incremental updates.
- Stores data in `data/raw/price/`.
- `save_dataset()`
- `load_dataset()`
- `update_price_history(symbol, provider)`: Incremental update logic (merges new data, validates, and saves).

#### [NEW] `src/api/main.py`
FastAPI application entry point.
- Exposes an endpoint `GET /price-history?symbol=BBCA.JK` that retrieves the full history from storage.

#### [NEW] `scripts/update_data.py`
A CLI script to easily update historical data for one or many symbols.

---

### Testing

#### [NEW] `tests/test_data_layer.py`
Unit tests using `pytest` for:
- Provider functionality
- Storage operations (saving, loading, incremental merging)
- Data validation logic

## Verification Plan

### Automated Tests
- Run `pytest` to verify provider, storage, incremental updates, and validation logic without hitting the live network repeatedly.

### Manual Verification
1. Run `python scripts/update_data.py --symbol BBCA.JK` to see it download the full history and create a Parquet file.
2. Run it again to verify it only fetches incremental/no data.
3. Start the FastAPI server using `uvicorn src.api.main:app --reload` and request `/price-history?symbol=BBCA.JK`.
4. Verify the backend returns the available historical dataset.
