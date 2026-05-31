import pandas as pd


def clip_score(series: pd.Series) -> pd.Series:
    return series.fillna(0).clip(lower=0, upper=100)


def percentile_low_is_good(series: pd.Series) -> pd.Series:
    return (1 - series.rank(pct=True, ascending=True)) * 100


def percentile_high_is_good(series: pd.Series) -> pd.Series:
    return series.rank(pct=True, ascending=True) * 100


def grade_from_score(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "E"
