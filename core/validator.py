"""
validator.py

Input validation, kept separate from both data loading and index math.
If the user does something invalid (no stocks selected, weights that
don't sum to 1, a date range with no data), this is the single place
that catches it and produces a human-readable message — rather than
letting a confusing pandas/NumPy error surface in the UI.
"""

import numpy as np


class ValidationResult:
    """Simple container so the caller can check .is_valid and read .messages."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, msg: str):
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)


class Validator:
    """Validates user selections before any index calculation runs."""

    @staticmethod
    def validate_selection(selected_tickers: list[str]) -> ValidationResult:
        result = ValidationResult()
        if not selected_tickers:
            result.add_error("Please select at least one stock.")
        elif len(selected_tickers) < 2:
            result.add_warning("Only one stock selected — the 'index' will just track that single stock.")
        return result

    @staticmethod
    def validate_weights(weights: dict[str, float]) -> ValidationResult:
        result = ValidationResult()
        total = sum(weights.values())
        # allow small floating point tolerance rather than requiring an exact 1.0
        if not np.isclose(total, 1.0, atol=1e-6):
            result.add_error(f"Weights must sum to 1.0 (currently sum to {total:.4f}).")
        if any(w < 0 for w in weights.values()):
            result.add_error("Weights cannot be negative.")
        return result

    @staticmethod
    def validate_price_matrix(price_matrix) -> ValidationResult:
        result = ValidationResult()
        if price_matrix.empty:
            result.add_error("No price data found for the selected stocks and date range.")
            return result

        missing_counts = price_matrix.isna().sum()
        for ticker, n_missing in missing_counts.items():
            if n_missing > 0:
                result.add_warning(
                    f"{ticker} has {n_missing} missing day(s) in this range — "
                    f"forward-filled from the last available close."
                )
        return result
