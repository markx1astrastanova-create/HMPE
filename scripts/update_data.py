import argparse
import logging
import os
import sys

# Ensure 'src' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_layer.provider import YahooFinanceProvider
from src.data_layer.storage import ParquetStorage, update_price_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Update Historical Market Data")
    parser.add_argument("--symbol", type=str, help="Single symbol to update (e.g. BBCA.JK)")
    parser.add_argument("--symbols", type=str, nargs="+", help="Multiple symbols to update")
    args = parser.parse_args()

    symbols_to_update = []
    if args.symbol:
        symbols_to_update.append(args.symbol)
    if args.symbols:
        symbols_to_update.extend(args.symbols)

    if not symbols_to_update:
        print("Please provide at least one symbol. Usage: python update_data.py --symbol BBCA.JK")
        return

    provider = YahooFinanceProvider()
    storage = ParquetStorage(base_dir=os.path.join(os.path.dirname(__file__), "..", "data", "raw", "price"))

    for sym in set(symbols_to_update):
        sym = sym.strip().upper()
        logging.info(f"Processing {sym}...")
        try:
            update_price_history(sym, provider, storage)
            logging.info(f"Finished {sym}")
        except Exception as e:
            logging.error(f"Failed to update {sym}: {e}")

if __name__ == "__main__":
    main()
