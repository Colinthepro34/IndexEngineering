"""
index_calculator.py

Implements the three required formulas, in order:

  1. Stock daily return:      r_i(t) = close_i(t) / close_i(t-1) - 1
  2. Index daily return:      r_index(t) = sum(w_i * r_i(t))
  3. Index level from base:   level(t) = level(t-1) * (1 + r_index(t))

This class takes a price matrix (wide: date x ticker) and a
WeightingStrategy object — it doesn't know or care which concrete
weighting subclass it received, only that it has a compute_weights()
method. That's the polymorphism paying off: adding a fourth weighting
scheme later needs zero changes here.
"""

import pandas as pd

from core.weighting import WeightingStrategy


class IndexCalculator:
    def __init__(self, price_matrix: pd.DataFrame, universe_df: pd.DataFrame,
                 strategy: WeightingStrategy, base_level: float = 100.0):
        self.price_matrix = price_matrix
        self.universe_df = universe_df
        self.strategy = strategy
        self.base_level = base_level

    def _handle_missing(self) -> pd.DataFrame:
        """
        Missing-data policy: forward-fill (carry the last known price
        forward). This is a simple, defensible choice for a short gap —
        it assumes the stock simply didn't trade that day rather than
        losing all value. Documented explicitly so it's not a silent
        decision.
        """
        return self.price_matrix.ffill()

    def compute_daily_returns(self) -> pd.DataFrame:
        """r_i(t) = close_i(t) / close_i(t-1) - 1, per ticker column."""
        clean_prices = self._handle_missing()
        return clean_prices.pct_change().dropna(how="all")

    def compute_index_series(self) -> dict:
        tickers = list(self.price_matrix.columns)
        weights = self.strategy.compute_weights(tickers, self.universe_df)

        daily_returns = self.compute_daily_returns()

        # r_index(t) = sum(w_i * r_i(t)) — weighted sum across tickers, per day
        weight_series = pd.Series(weights)
        index_daily_return = daily_returns[weight_series.index].mul(weight_series, axis=1).sum(axis=1)

        # level(t) = level(t-1) * (1 + r_index(t)), starting from base_level
        index_level = (1 + index_daily_return).cumprod() * self.base_level
        # prepend the base level on the first date in the price matrix
        first_date = self.price_matrix.index.min()
        index_level = pd.concat([
            pd.Series([self.base_level], index=[first_date]),
            index_level
        ]).sort_index()

        cumulative_return = (index_level.iloc[-1] / index_level.iloc[0]) - 1

        return {
            "weights": weights,
            "daily_returns": daily_returns,
            "index_daily_return": index_daily_return,
            "index_level": index_level,
            "cumulative_return": cumulative_return,
        }
