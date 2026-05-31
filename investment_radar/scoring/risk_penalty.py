import pandas as pd


def calculate_risk_penalty(financials: pd.DataFrame, prices: pd.DataFrame, event_map: pd.DataFrame) -> pd.DataFrame:
    latest_fin = financials.sort_values(["year", "quarter"]).groupby("ticker").tail(1).copy()
    latest_price = prices.sort_values("date").groupby("ticker").tail(1).copy()
    frame = latest_fin.merge(latest_price[["ticker", "return_1m"]], on="ticker", how="left")
    frame["debt_ratio"] = frame["liabilities"] / frame["assets"].replace(0, pd.NA)
    speculative = event_map[event_map["relation_type"].eq("SPECULATIVE")].groupby("ticker").size().rename("speculative_count")
    frame = frame.merge(speculative, on="ticker", how="left")
    frame["risk_penalty"] = (
        frame["debt_ratio"].fillna(0).clip(0, 1) * 20
        + frame["return_1m"].fillna(0).clip(lower=0) / 2
        + frame["speculative_count"].fillna(0) * 8
    ).clip(0, 35)
    return frame[["ticker", "risk_penalty"]]
