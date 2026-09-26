"""
data_loader.py

Responsible for one thing only: reading the raw CSV data off disk and
handing back clean pandas objects. Keeping this separate from the
index math (index_calculator.py) and from input validation
(validator.py) is a deliberate separation-of-concerns choice — each
class has a single, explainable job.
"""

import pandas as pd


class DataLoader:
    """Loads the stock universe and price history from CSV files."""

    def __init__(self, universe_path: str, prices_path: str):
        self.universe_path = universe_path
        self.prices_path = prices_path

    def load_universe(self) -> pd.DataFrame:
        """Returns the 30-stock universe: ticker, company_name, sector, market_cap."""
        df = pd.read_csv(self.universe_path)
        required_cols = {"ticker", "company_name", "sector", "market_cap"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"stock_universe.csv is missing required columns: {missing}")
        return df

    def load_prices(self) -> pd.DataFrame:
        """Returns long-format daily close prices: date, ticker, close_price."""
        df = pd.read_csv(self.prices_path, parse_dates=["date"])
        required_cols = {"date", "ticker", "close_price"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"stock_prices.csv is missing required columns: {missing}")
        return df

    def get_price_matrix(self, tickers: list[str], start_date, end_date) -> pd.DataFrame:
        """
        Pivots the long price table into a wide date x ticker matrix for
        just the selected tickers and date range. Wide format is what the
        return/index calculations actually need.
        """
        prices = self.load_prices()
        mask = (
            prices["ticker"].isin(tickers)
            & (prices["date"] >= pd.to_datetime(start_date))
            & (prices["date"] <= pd.to_datetime(end_date))
        )
        subset = prices.loc[mask]
        matrix = subset.pivot(index="date", columns="ticker", values="close_price").sort_index()
        return matrix
