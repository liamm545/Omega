import numpy as np
import pandas as pd


def cumulative_return(returns: pd.Series) -> float:
    return float((1 + returns.fillna(0)).prod() - 1)


def cagr(returns: pd.Series, periods_per_year: int = 252) -> float:
    if returns.empty:
        return 0.0
    total = cumulative_return(returns)
    years = max(len(returns) / periods_per_year, 1 / periods_per_year)
    return float((1 + total) ** (1 / years) - 1)


def volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    value = returns.fillna(0).std() * np.sqrt(periods_per_year)
    return 0.0 if pd.isna(value) else float(value)


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    vol = volatility(returns, periods_per_year)
    if vol == 0 or pd.isna(vol):
        return 0.0
    return float((returns.mean() * periods_per_year - risk_free_rate) / vol)


def max_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    peak = equity_curve.cummax()
    drawdown = equity_curve / peak - 1
    return float(drawdown.min())


def win_rate(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return 0.0
    return float((clean > 0).mean())


def average_gain_loss(returns: pd.Series) -> dict:
    gains = returns[returns > 0]
    losses = returns[returns < 0]
    return {
        "average_gain": float(gains.mean()) if not gains.empty else 0.0,
        "average_loss": float(losses.mean()) if not losses.empty else 0.0,
    }


def summarize_performance(result: pd.DataFrame) -> dict:
    if result.empty:
        return {}
    returns = result["strategy_return"].fillna(0)
    benchmark = result["benchmark_return"].fillna(0)
    equity = (1 + returns).cumprod()
    summary = {
        "cagr": cagr(returns),
        "cumulative_return": cumulative_return(returns),
        "volatility": volatility(returns),
        "sharpe_ratio": sharpe_ratio(returns),
        "mdd": max_drawdown(equity),
        "win_rate": win_rate(returns),
        "excess_return": cumulative_return(returns) - cumulative_return(benchmark),
    }
    summary.update(average_gain_loss(returns))
    return summary
