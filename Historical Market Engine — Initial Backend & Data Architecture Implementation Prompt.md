# Historical Market Engine — Initial Backend & Data Architecture Implementation

You are the implementation agent for the **Historical Market Engine (HME)** project.

Your job in this task is to implement the technical foundation of the HME based on the existing project concept. **Do not redesign the research methodology unless you encounter a genuine technical contradiction.** If something is ambiguous, inspect the existing project first and preserve the intended architecture.

## 1. Core Objective

Build the backend data layer for HME so that the application can work with **large amounts of historical market price data**, rather than being limited to a small number of bars returned by a charting API.

For the initial implementation, use:

**`yfinance` as the primary market-data library.**

The system must be designed around the assumption that HME needs historical OHLCV data extending as far back as the available data allows.

The important distinction is:

> Backend/data layer = full historical dataset  
> Frontend/chart = visualization of the stored historical dataset

Do NOT implement a system where the frontend only receives the most recent 60 bars.

---

# 2. First: Inspect Existing Repository

Before modifying anything:

1. Inspect the entire repository structure.
2. Identify:
   - existing backend
   - existing frontend
   - current data-fetching implementation
   - existing indicators/features
   - existing database/cache/storage
   - configuration files
   - requirements/dependencies
   - existing tests
3. Determine whether the project is currently Python-only, Streamlit-based, or already partially migrated toward another frontend/backend architecture.

Do not unnecessarily rewrite existing working components.

Create a short internal implementation plan based on the repository before making changes.

---

# 3. Data Source

Replace/abstract the current historical price-data dependency with a proper data-provider layer.

Use:

```python
import yfinance as yf
```

The architecture should NOT hard-code yfinance throughout the application.

Create an abstraction such as:

```text
Data Provider
    └── Yahoo Finance / yfinance implementation
```

This allows another provider to be added later without rewriting the HME engine.

For example:

```python
class MarketDataProvider:
    def get_price_history(self, symbol, start=None, end=None, interval="1d"):
        ...
```

Then implement:

```python
class YahooFinanceProvider(MarketDataProvider):
    ...
```

Use daily data for the initial HME implementation unless the existing project explicitly requires another timeframe.

---

# 4. Historical Data Requirement

The primary requirement is:

## Fetch as much historical daily data as reasonably available.

Do NOT use:

```python
period="1mo"
```

or another short period simply because the frontend only needs a limited display window.

Prefer:

```python
period="max"
```

when appropriate.

Alternatively use explicit `start` / `end` dates if the existing architecture requires deterministic date ranges.

The resulting dataset should contain, where available:

- Date
- Open
- High
- Low
- Close
- Adjusted Close
- Volume

Preserve the timestamp/date correctly.

Do not silently discard historical observations.

---

# 5. Important: Full Backend Data vs Frontend Display

Implement the architecture so that:

```text
Yahoo Finance
      ↓
Data Provider
      ↓
Raw Historical Dataset
      ↓
Local Storage / Cache
      ↓
Feature Engineering
      ↓
Historical Market Engine
      ↓
API / Backend Response
      ↓
Frontend
```

The backend should retain the complete historical dataset.

The frontend may choose to:

- display the full history
- zoom into a specific period
- select a date range
- display recent N days
- display the entire available history

But this must be a **frontend visualization choice**, NOT a backend data limitation.

For example:

```text
Backend:
2010 → 2026
        ↓
Frontend:
2010 → 2026
or
2020 → 2026
or
2025 → 2026
or
last 200 trading days
```

All of these should operate on the same stored historical dataset.

---

# 6. Storage / Caching

Do NOT repeatedly download the entire historical dataset from Yahoo Finance every time the application starts or every time the user changes a chart.

Implement a local historical-data cache.

For the first implementation, prefer a simple robust solution such as:

```text
data/
    raw/
    processed/
```

with Parquet files where practical.

Example:

```text
data/raw/price/BBCA.JK.parquet
data/raw/price/BBRI.JK.parquet
data/raw/price/BMRI.JK.parquet
data/raw/price/^JKSE.parquet
```

The exact structure may be adjusted to match the existing repository.

Use Parquet because HME will eventually work with many securities and potentially millions of rows.

The storage layer should support:

```text
download full history initially
        ↓
save locally
        ↓
future execution
        ↓
detect latest stored date
        ↓
download only missing/new data
        ↓
append/update dataset
```

Avoid unnecessary full re-downloads.

---

# 7. Incremental Update Logic

Implement a reusable function similar to:

```python
update_price_history(symbol)
```

Expected behavior:

### First run

If no local dataset exists:

```text
download maximum available history
save dataset
```

### Subsequent run

If historical data already exists:

```text
read latest stored date
        ↓
request newer data
        ↓
merge
        ↓
deduplicate by trading date
        ↓
sort chronologically
        ↓
save
```

Do not create duplicate dates.

Use the trading date as the primary temporal key for daily data.

---

# 8. Symbol Handling

The provider should support Indonesian equities.

Examples:

```text
BBCA.JK
BBRI.JK
BMRI.JK
```

and IHSG:

```text
^JKSE
```

Do not assume that every symbol follows the same Yahoo Finance convention.

Create a clean symbol configuration/mapping layer so symbols are easy to modify later.

Do not hard-code hundreds of symbols directly inside business logic.

---

# 9. Data Validation

Every downloaded dataset must be validated before being accepted.

At minimum check:

- Date exists
- Date is unique
- Date is sorted ascending
- OHLC columns exist
- Open/High/Low/Close are numeric
- High >= Low
- High >= Open
- High >= Close
- Low <= Open
- Low <= Close
- no impossible negative prices
- reasonable missing-value handling
- duplicate dates are removed

Do not blindly drop problematic rows.

If data quality problems occur, log them clearly.

---

# 10. Trading Calendar Awareness

HME is a historical market engine, so calendar handling is important.

Do NOT treat calendar days as trading days.

The price dataset itself should define actual observed trading sessions.

For example:

```text
Friday
Saturday
Sunday
Monday
```

should contain only actual market observations.

The system should eventually support a dedicated trading-calendar layer so that historical windows are based on **trading sessions**, not naive calendar-day subtraction.

Do not implement complicated Indonesian holiday logic unless the existing project already contains it.

For this stage, create the architecture/interface so the calendar system can be expanded later.

---

# 11. Data Layer API

Create clean functions for other parts of HME to consume.

For example:

```python
get_price_history(
    symbol,
    start=None,
    end=None
)
```

and:

```python
update_price_history(symbol)
```

Potentially:

```python
get_latest_date(symbol)
```

```python
get_available_date_range(symbol)
```

```python
get_universe_history(symbols)
```

Use appropriate names based on the existing codebase.

The rest of HME should not need to know whether the data came from:

- yfinance
- Parquet
- database
- another provider

That complexity belongs inside the data layer.

---

# 12. Historical Engine Compatibility

The eventual HME logic will compare the current market state against historical states.

Therefore, the data layer must preserve the full chronological history.

Do NOT prematurely truncate the data to:

```text
last 60 observations
```

or:

```text
last 252 observations
```

The historical engine will decide what historical window it needs.

For example, if the engine eventually needs:

```text
current state
↓
lookback 60 trading days
↓
search entire historical dataset
↓
find similar historical states
↓
measure forward returns
```

the backend must make the entire historical dataset available.

---

# 13. Frontend Requirements

If an existing frontend/chart exists:

- connect it to the backend historical dataset
- make the chart capable of displaying the full available history
- support zooming/range selection
- do not artificially truncate the data to 60 bars
- do not download only the currently visible range unless the backend architecture explicitly requires server-side pagination

The frontend should be able to request something conceptually like:

```text
GET /price-history?symbol=BBCA.JK
```

and receive the available historical dataset.

If the dataset becomes too large for practical browser rendering, implement a sensible visualization optimization such as:

- server-side range selection
- downsampling for visualization
- lazy loading

BUT:

**Never destroy or truncate the underlying historical dataset merely for frontend performance.**

---

# 14. Separation of Concerns

Maintain this separation:

```text
Data Provider
    ↓
Storage
    ↓
Data Validation
    ↓
Feature Engineering
    ↓
Historical Market Engine
    ↓
API
    ↓
Frontend
```

Do not put yfinance calls inside chart components.

Do not put historical matching logic inside the data downloader.

Do not put data-cleaning logic inside the frontend.

Keep each responsibility isolated.

---

# 15. Error Handling

Yahoo Finance/network failures must not crash the entire application unnecessarily.

Handle:

- connection failure
- timeout
- empty response
- invalid ticker
- rate limiting
- malformed data
- missing columns
- partial download

Log useful information.

If cached historical data exists and Yahoo Finance is temporarily unavailable, the application should preferably continue operating using the last valid cached dataset.

---

# 16. Dependency Management

Add only the dependencies actually required.

At minimum:

```text
yfinance
pandas
pyarrow
```

if Parquet is used.

Respect the existing dependency-management system of the repository.

Do not install unnecessary frameworks.

---

# 17. Testing

Create tests for at least:

### Data provider

```text
fetch valid symbol
fetch invalid symbol
empty response
```

### Storage

```text
save dataset
load dataset
update dataset
duplicate removal
chronological sorting
```

### Validation

```text
valid OHLC
invalid OHLC
missing values
duplicate dates
```

### Incremental update

Test that existing historical data is not unnecessarily duplicated when new data is added.

Tests should not require repeatedly hitting Yahoo Finance if avoidable. Mock the external provider where appropriate.

---

# 18. Documentation

Document:

1. How to install dependencies.
2. How to download initial historical data.
3. How to update historical data.
4. Where raw data is stored.
5. How symbols are configured.
6. How the frontend accesses historical data.
7. How another data provider could be added later.

---

# 19. Do NOT Do These Things

Do NOT:

- limit historical data to 60 bars
- fetch data only when the chart requests it
- hard-code yfinance throughout the application
- store the entire dataset only in browser memory
- discard old data during updates
- use calendar days as trading-session indices
- rewrite the HME methodology
- build a fake prediction model just to make the UI work
- introduce unnecessary ML components
- fabricate missing historical data
- silently fill missing market observations with fake prices

The current task is **data/backend infrastructure**, not prediction-model development.

---

# 20. Deliverables

After implementation, provide:

### A. Architecture summary

Explain:

```text
data source
→ provider
→ storage
→ update mechanism
→ feature layer
→ API
→ frontend
```

### B. Files changed

List every file created or modified.

### C. How to run

Give exact commands needed to:

1. install dependencies
2. initialize/download historical data
3. update historical data
4. start backend
5. start frontend

depending on the existing repository architecture.

### D. Validation

Report:

- number of symbols tested
- earliest available date
- latest available date
- number of rows
- whether duplicate dates exist
- whether OHLC validation passed
- whether incremental update works
- whether frontend can display more than 60 bars

### E. Important implementation decisions

Explicitly mention any place where you had to deviate from this specification and why.

---

# Final Principle

The most important architectural requirement is:

**HME must own/access the full historical dataset. The chart is merely a view of that dataset.**

We are building a historical market-analysis engine, so historical data availability is a core backend asset, not something that should be constrained by the frontend chart's visible range.

Implement this foundation cleanly so that the next stage can build the actual Historical Market Engine feature-engineering and historical-state matching logic on top of it.