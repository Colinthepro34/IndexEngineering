# Custom Index Builder (Price Return Only)

A small analytical application that builds a custom equity index from
a 30-stock dummy universe and computes a Price Return Index over a
user-selected date range and weighting method.

## Project Overview

The user picks any subset of stocks from a 30-stock universe, chooses
a weighting method (Equal, Market-Cap, or Custom), and a date range.
The app computes daily stock returns, combines them into a weighted
daily index return, and compounds those into an index level series
starting from a base of 100 — along with cumulative return and
validation warnings for any data issues.

## How to Run

```bash
pip install streamlit pandas numpy plotly
python generate_data.py      # creates data/stock_universe.csv and data/stock_prices.csv
streamlit run app.py
```

The app opens in your browser (default: http://localhost:8501).

## Architecture Choices

**UI — Streamlit.** Chosen because it's Python-native end to end: the
same language runs the UI and the analytics, with no separate
JS/React frontend to build and keep in sync. It renders directly in a
browser, satisfying the web-UI requirement, and it's fast to build an
interactive tool with sliders/selectors around an analytical core —
which is exactly this exercise's shape.

**Backend — plain Python + pandas/NumPy**, organized as a small set
of single-responsibility classes rather than one script:

| File | Responsibility |
|---|---|
| `core/data_loader.py` | Reads CSVs, validates required columns, reshapes long → wide price matrix |
| `core/validator.py` | Validates user selections, weights, and the resulting price data — independent of both loading and calculation |
| `core/weighting.py` | `WeightingStrategy` abstract base class + `EqualWeighting`, `MarketCapWeighting`, `CustomWeighting` subclasses |
| `core/index_calculator.py` | Implements the three required formulas; takes a `WeightingStrategy` object without knowing which concrete subclass it is |
| `app.py` | Thin UI layer — wires user inputs to the classes above and renders results |

This separation means the UI could be swapped for Flask/FastAPI later,
or a fourth weighting scheme added, without touching the other layers
— each class has exactly one reason to change.

**UI ↔ Backend interaction:** Streamlit re-runs `app.py` top-to-bottom
on every interaction. `app.py` instantiates `DataLoader` and a
`WeightingStrategy` subclass based on the sidebar selections, passes
them into `IndexCalculator`, and renders the returned dict directly —
there's no separate API layer, since Streamlit's execution model makes
one unnecessary for a tool this size.

## Weighting Method Implemented

All three are implemented via a common `WeightingStrategy` interface
(polymorphism — see "OOP" below):

- **Equal Weight:** every selected stock gets `1/N`.
- **Market-Cap Weight:** weight proportional to each stock's
  `market_cap` field from the universe data.
- **Custom Weight:** user enters relative weights per stock; the app
  normalizes them to sum to 1 regardless of the raw values entered.

## Price Return Formula

```
r_i(t)      = close_i(t) / close_i(t-1) - 1        # per-stock daily return
r_index(t)  = Σ ( w_i * r_i(t) )                    # weighted index daily return
level(t)    = level(t-1) * (1 + r_index(t))         # compounded index level, base = 100
```

Implemented in `IndexCalculator.compute_index_series()`.

## Missing-Data Handling

The dummy price data includes one deliberately missing day (ticker
`DUM07`) to exercise this path. Policy: **forward-fill** — carry the
last known close price forward for the missing day, via
`price_matrix.ffill()`. This assumes the stock simply didn't trade
that day rather than losing value, which is a reasonable default for
a short single-day gap. The `Validator` surfaces a warning in the UI
whenever a selected stock had missing data filled, so it's visible
rather than silent.

## OOP in This Project

- **Classes/objects:** `DataLoader`, `Validator`, `IndexCalculator`,
  and each weighting strategy are all classes instantiated as objects
  in `app.py`.
- **Encapsulation:** each class exposes a small public method surface
  (e.g., `IndexCalculator.compute_index_series()`) and keeps its
  internal steps (like `_handle_missing()`) private to that class.
- **Inheritance:** `EqualWeighting`, `MarketCapWeighting`, and
  `CustomWeighting` all inherit from the abstract `WeightingStrategy`
  base class.
- **Polymorphism:** `IndexCalculator` calls `self.strategy.compute_weights(...)`
  without knowing which concrete subclass it holds — swapping the
  weighting method in the UI swaps which subclass gets passed in, and
  the calculator code never changes.

## Limitations

- No support for index rebalancing over time — weights are computed
  once at the start of the selected range and held fixed, rather than
  being recalculated periodically (e.g., quarterly) as a real index
  would.
- Forward-fill is a simple missing-data policy; it doesn't distinguish
  "stock didn't trade" from "data genuinely absent," and could mask a
  longer gap if one existed.
- No total-return variant (dividends/corporate actions aren't
  modeled) — this is explicitly a *price* return index only, per the
  exercise scope.
- Custom weighting has no upper bound per stock (no concentration
  limit), which a real index methodology would typically enforce.

## Future Improvements

- Add periodic rebalancing (e.g., recompute weights monthly) and show
  turnover between rebalance dates.
- Add a Total Return variant incorporating a dummy dividend yield per
  stock.
- Add float-adjusted market-cap weighting (using a free-float factor
  per stock) instead of full market-cap.
- Add unit tests for `IndexCalculator` and `Validator` (currently
  verified manually; a `tests/` folder with pytest would be the
  natural next step).
