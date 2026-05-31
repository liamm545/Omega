import pandas as pd

from backtesting.portfolio_backtester import run_score_top_n_backtest


def run_factor_backtest(scores: pd.DataFrame, prices: pd.DataFrame, factor: str, top_n: int = 5) -> pd.DataFrame:
    ranked = scores.sort_values(factor, ascending=False) if factor in scores.columns else scores
    return run_score_top_n_backtest(ranked, prices, top_n=top_n)
