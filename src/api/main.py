from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

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
def get_price_history(symbol: str, update: bool = False):
    """
    Retrieve the historical price data for a symbol.
    If 'update' is True or data does not exist, it will fetch updates first.
    """
    symbol = symbol.strip().upper()
    
    # Try to load existing data
    df = storage.load_dataset(symbol)
    
    # If forced update or no data exists, do an update
    if update or df.empty:
        df = update_price_history(symbol, provider, storage)
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")

    # Convert Date to string for JSON serialization
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    # Fill NaN to avoid JSON errors
    df = df.fillna(0)
    
    # Return as list of dictionaries
    return df.to_dict(orient="records")
