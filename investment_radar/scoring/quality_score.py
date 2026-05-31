import pandas as pd

from scoring.common import clip_score, percentile_high_is_good


def calculate_quality_score(financials: pd.DataFrame) -> pd.DataFrame:
    latest = financials.sort_values(["year", "quarter"]).groupby("ticker").tail(1).copy()
    latest["roe"] = latest["net_income"] / latest["equity"].replace(0, pd.NA)
    latest["op_margin"] = latest["operating_profit"] / latest["revenue"].replace(0, pd.NA)
    latest["fcf_margin"] = latest["free_cash_flow"] / latest["revenue"].replace(0, pd.NA)
    latest["debt_ratio_inverse"] = 1 - latest["liabilities"] / latest["assets"].replace(0, pd.NA)

    components = [
        percentile_high_is_good(latest["roe"]),
        percentile_high_is_good(latest["op_margin"]),
        percentile_high_is_good(latest["fcf_margin"]),
        percentile_high_is_good(latest["debt_ratio_inverse"]),
    ]
    latest["quality_score"] = clip_score(pd.concat(components, axis=1).mean(axis=1))
    return latest[["ticker", "quality_score"]]
