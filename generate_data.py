"""
generate_data.py

Generates dummy data for the Custom Index Builder exercise:
  - data/stock_universe.csv : ticker, company_name, sector, market_cap
  - data/stock_prices.csv   : date, ticker, close_price

The data is synthetic but internally consistent: each stock follows a
random-walk-with-drift price path so returns look realistic, and one
stock (DUM07) has a deliberately missing day of data so the app's
missing-data handling can be demonstrated.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)  # reproducibility — important to be able to explain this

SECTORS = ["Technology", "Financials", "Healthcare", "Energy", "Consumer"]
N_STOCKS = 30
N_DAYS = 90  # ~ one quarter of trading days

# ---------- 1. Stock universe ----------
tickers = [f"DUM{str(i).zfill(2)}" for i in range(1, N_STOCKS + 1)]
companies = [f"Dummy Corp {i}" for i in range(1, N_STOCKS + 1)]
sectors = np.random.choice(SECTORS, size=N_STOCKS)

# market_cap in crores — a numeric field used for market-cap weighting
market_caps = np.round(np.random.uniform(500, 50000, size=N_STOCKS), 2)

universe = pd.DataFrame({
    "ticker": tickers,
    "company_name": companies,
    "sector": sectors,
    "market_cap": market_caps,
})
universe.to_csv("data/stock_universe.csv", index=False)

# ---------- 2. Daily close prices ----------
start_date = datetime(2026, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(N_DAYS)]
# keep only weekdays, like a real market calendar
dates = [d for d in dates if d.weekday() < 5]

rows = []
for ticker in tickers:
    price = np.random.uniform(50, 3000)  # random starting price
    drift = np.random.uniform(-0.0003, 0.0006)
    vol = np.random.uniform(0.01, 0.03)
    for d in dates:
        price = price * (1 + np.random.normal(drift, vol))
        rows.append({"date": d.strftime("%Y-%m-%d"), "ticker": ticker, "close_price": round(price, 2)})

prices = pd.DataFrame(rows)

# Deliberately introduce one missing day for one ticker, to exercise
# the missing-data handling path (documented in the README).
mask = ~((prices["ticker"] == "DUM07") & (prices["date"] == dates[10].strftime("%Y-%m-%d")))
prices = prices[mask]

prices.to_csv("data/stock_prices.csv", index=False)

print(f"Generated {len(universe)} stocks and {len(prices)} price rows "
      f"across {len(dates)} trading days ({dates[0].date()} to {dates[-1].date()}).")
