from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import numpy as np
import pandas as pd
from typing import Optional

from src.data_layer.provider import YahooFinanceProvider
from src.data_layer.storage import ParquetStorage, update_price_history

app = FastAPI(title="Historical Market Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons for the data layer
provider = YahooFinanceProvider()
storage = ParquetStorage(base_dir=os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "price"))

@app.get("/")
def health_check():
    return {"status": "ok", "message": "HMPE Backend is running"}

@app.get("/price-history")
def get_price_history(symbol: str, start: Optional[str] = Query(None), end: Optional[str] = Query(None)):
    """
    Retrieve the historical price data for a symbol.
    Does NOT trigger external downloads.
    """
    symbol = symbol.strip().upper()
    
    # Load existing data
    df = storage.load_dataset(symbol)
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No local historical data found for {symbol}. Run an update first.")

    # Apply date filters if provided
    if start:
        df = df[df['Date'] >= pd.to_datetime(start)]
    if end:
        df = df[df['Date'] <= pd.to_datetime(end)]

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol} in the given date range.")

    # Convert Date to string for JSON serialization
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    # Replace NaN with None so it serializes to JSON null instead of 0
    df = df.replace({np.nan: None})
    
    # Return as list of dictionaries
    return df.to_dict(orient="records")
