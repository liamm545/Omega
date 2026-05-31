import pandas as pd

from scoring.common import clip_score, percentile_high_is_good


def calculate_improvement_score(financials: pd.DataFrame) -> pd.DataFrame:
    latest = financials.sort_values(["year", "quarter"]).groupby("ticker").tail(1).copy()
    previous = financials.sort_values(["year", "quarter"]).groupby("ticker").nth(-2).reset_index()
    frame = latest.merge(previous, on="ticker", how="left", suffixes=("", "_prev"))

    frame["revenue_growth"] = (frame["revenue"] - frame["revenue_prev"]) / frame["revenue_prev"].replace(0, pd.NA)
    frame["op_growth"] = (frame["operating_profit"] - frame["operating_profit_prev"]) / frame["operating_profit_prev"].replace(0, pd.NA)
    frame["margin"] = frame["operating_profit"] / frame["revenue"].replace(0, pd.NA)
    frame["margin_prev"] = frame["operating_profit_prev"] / frame["revenue_prev"].replace(0, pd.NA)
    frame["margin_improvement"] = frame["margin"] - frame["margin_prev"]
    frame["turnaround"] = ((frame["operating_profit"] > 0) & (frame["operating_profit_prev"] <= 0)).astype(int) * 100

    components = [
        percentile_high_is_good(frame["revenue_growth"]),
        percentile_high_is_good(frame["op_growth"]),
        percentile_high_is_good(frame["margin_improvement"]),
        frame["turnaround"],
    ]
    frame["improvement_score"] = clip_score(pd.concat(components, axis=1).mean(axis=1))
    return frame[["ticker", "improvement_score"]]
