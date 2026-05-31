import pandas as pd

from scoring.common import clip_score, percentile_low_is_good


def calculate_valuation_score(stocks: pd.DataFrame, valuation: pd.DataFrame, financials: pd.DataFrame) -> pd.DataFrame:
    latest_fin = financials.sort_values(["year", "quarter"]).groupby("ticker").tail(1)
    frame = valuation.merge(stocks[["ticker", "sector"]], on="ticker", how="left")
    frame = frame.merge(latest_fin[["ticker", "net_income"]], on="ticker", how="left")

    metrics = []
    for metric in ["per", "pbr", "psr", "ev_ebitda"]:
        score = frame.groupby("sector")[metric].transform(percentile_low_is_good)
        metrics.append(score)

    frame["valuation_score"] = clip_score(pd.concat(metrics, axis=1).mean(axis=1))
    frame.loc[frame["net_income"].fillna(0) <= 0, "valuation_score"] *= 0.45
    return frame[["ticker", "valuation_score"]]
