import pandas as pd

from scoring.common import clip_score, percentile_high_is_good


def calculate_momentum_score(prices: pd.DataFrame) -> pd.DataFrame:
    latest = prices.sort_values("date").groupby("ticker").tail(1).copy()
    components = [
        percentile_high_is_good(latest["return_1m"]),
        percentile_high_is_good(latest["return_3m"]),
        percentile_high_is_good(latest["trading_value"]),
    ]
    latest["momentum_score"] = clip_score(pd.concat(components, axis=1).mean(axis=1))
    return latest[["ticker", "momentum_score"]]
