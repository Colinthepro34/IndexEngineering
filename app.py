"""
app.py

Streamlit front end for the Custom Index Builder.

Why Streamlit: it's a Python-native web framework, so the UI and the
backend analytical logic share one language end to end — no separate
JS frontend/Python backend split to maintain, which matters for a
small analytical tool like this. It also renders directly to a
browser, satisfying the "must be viewable in a web browser" requirement.

This file is intentionally thin — it only handles UI layout and wiring
user inputs to the core/ classes. All the actual logic (loading,
validating, calculating) lives in core/, so the UI could be swapped
for a different framework later without touching the analytics.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.data_loader import DataLoader
from core.validator import Validator
from core.weighting import EqualWeighting, MarketCapWeighting, CustomWeighting
from core.index_calculator import IndexCalculator

st.set_page_config(page_title="Custom Index Builder", layout="wide")
st.title("Custom Index Builder — Price Return Index")

loader = DataLoader("data/stock_universe.csv", "data/stock_prices.csv")
universe = loader.load_universe()
all_prices = loader.load_prices()

# ---------- Sidebar: user inputs ----------
st.sidebar.header("1. Select Stocks")
st.sidebar.caption("Choose any number of stocks from the 30-stock universe.")
selected = st.sidebar.multiselect(
    "Stock universe",
    options=universe["ticker"] + " — " + universe["company_name"],
    default=list((universe["ticker"] + " — " + universe["company_name"]).iloc[:5]),
)
selected_tickers = [s.split(" — ")[0] for s in selected]

st.sidebar.header("2. Weighting Method")
weighting_choice = st.sidebar.radio(
    "Method", ["Equal Weight", "Market-Cap Weight", "Custom Weight"]
)

custom_weights_input = {}
if weighting_choice == "Custom Weight" and selected_tickers:
    st.sidebar.caption("Enter relative weights — they'll be normalized to sum to 1.")
    for t in selected_tickers:
        custom_weights_input[t] = st.sidebar.number_input(f"{t}", min_value=0.0, value=1.0, step=0.5)

st.sidebar.header("3. Date Range")
min_date, max_date = all_prices["date"].min(), all_prices["date"].max()
date_range = st.sidebar.date_input(
    "Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

generate = st.sidebar.button("Generate", type="primary")

# ---------- Main panel ----------
with st.expander("View full 30-stock universe"):
    st.dataframe(universe, use_container_width=True)

if generate:
    selection_check = Validator.validate_selection(selected_tickers)
    if not selection_check.is_valid:
        for e in selection_check.errors:
            st.error(e)
    else:
        for w in selection_check.warnings:
            st.warning(w)

        if len(date_range) != 2:
            st.error("Please select a valid start and end date.")
        else:
            start_date, end_date = date_range
            price_matrix = loader.get_price_matrix(selected_tickers, start_date, end_date)

            price_check = Validator.validate_price_matrix(price_matrix)
            if not price_check.is_valid:
                for e in price_check.errors:
                    st.error(e)
            else:
                for w in price_check.warnings:
                    st.warning(w)

                # --- pick the strategy object: this is the polymorphism in action ---
                if weighting_choice == "Equal Weight":
                    strategy = EqualWeighting()
                elif weighting_choice == "Market-Cap Weight":
                    strategy = MarketCapWeighting()
                else:
                    strategy = CustomWeighting(custom_weights_input)

                weight_check = Validator.validate_weights(strategy.compute_weights(selected_tickers, universe))
                if not weight_check.is_valid:
                    for e in weight_check.errors:
                        st.error(e)
                else:
                    calc = IndexCalculator(price_matrix, universe, strategy)
                    result = calc.compute_index_series()

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=result["index_level"].index, y=result["index_level"].values,
                            mode="lines", name="Index Level",
                        ))
                        fig.update_layout(
                            title="Custom Price Return Index (Base = 100)",
                            xaxis_title="Date", yaxis_title="Index Level",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        st.metric("Cumulative Return", f"{result['cumulative_return']*100:.2f}%")
                        st.metric("Base Level", f"{100:.2f}")
                        st.metric("End Level", f"{result['index_level'].iloc[-1]:.2f}")

                    st.subheader("Weights Used")
                    st.dataframe(pd.DataFrame(result["weights"].items(), columns=["Ticker", "Weight"]))

                    with st.expander("View daily index returns"):
                        st.dataframe(result["index_daily_return"].rename("Daily Return"))
else:
    st.info("Select stocks, a weighting method, and a date range in the sidebar, then click **Generate**.")
