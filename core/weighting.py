"""
weighting.py

This module is the clearest demonstration of OOP in the project.

WeightingStrategy is an abstract base class defining one contract:
`compute_weights(tickers, universe_df) -> dict[ticker, weight]`.
EqualWeighting, MarketCapWeighting, and CustomWeighting each implement
that same method differently — this is polymorphism: the calling code
(index_calculator.py) calls `.compute_weights(...)` on whatever
strategy object it was given, without needing to know or care which
concrete subclass it actually is.
"""

from abc import ABC, abstractmethod


class WeightingStrategy(ABC):
    """Abstract base class — defines the interface every weighting scheme must follow."""

    @abstractmethod
    def compute_weights(self, tickers: list[str], universe_df) -> dict[str, float]:
        """Must return a dict of {ticker: weight}, where weights sum to 1.0."""
        raise NotImplementedError


class EqualWeighting(WeightingStrategy):
    """Every selected stock gets the same weight: 1/N."""

    def compute_weights(self, tickers: list[str], universe_df) -> dict[str, float]:
        n = len(tickers)
        return {t: 1.0 / n for t in tickers}


class MarketCapWeighting(WeightingStrategy):
    """Weight proportional to each stock's market capitalization."""

    def compute_weights(self, tickers: list[str], universe_df) -> dict[str, float]:
        subset = universe_df[universe_df["ticker"].isin(tickers)]
        total_cap = subset["market_cap"].sum()
        return {
            row["ticker"]: row["market_cap"] / total_cap
            for _, row in subset.iterrows()
        }


class CustomWeighting(WeightingStrategy):
    """User-supplied weights, normalized to sum to 1.0 if they don't already."""

    def __init__(self, raw_weights: dict[str, float]):
        self.raw_weights = raw_weights

    def compute_weights(self, tickers: list[str], universe_df) -> dict[str, float]:
        total = sum(self.raw_weights.get(t, 0) for t in tickers)
        if total == 0:
            raise ValueError("Custom weights sum to zero — cannot normalize.")
        return {t: self.raw_weights.get(t, 0) / total for t in tickers}
