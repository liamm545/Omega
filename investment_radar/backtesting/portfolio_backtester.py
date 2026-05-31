import pandas as pd


HORIZON_TO_DAYS = {
    "1W": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
}


def run_score_top_n_backtest(
    scores: pd.DataFrame,
    prices: pd.DataFrame,
    top_n: int = 5,
    rebalance: str = "1M",
    transaction_cost: float = 0.001,
    benchmark_ticker: str = "KOSPI",
) -> pd.DataFrame:
    """Equal-weight top-N score backtest.

    Uses score information available at each rebalance date only. If the sample
    dataset has one date, it returns a one-row diagnostic result instead of
    fabricating history.
    """
    if scores.empty or prices.empty:
        return pd.DataFrame()

    price = prices.copy()
    price["date"] = pd.to_datetime(price["date"])
    unique_dates = sorted(price["date"].unique())
    if len(unique_dates) < 2:
        selected = scores.sort_values("total_score", ascending=False).head(top_n)
        return pd.DataFrame(
            [
                {
                    "date": unique_dates[0] if unique_dates else pd.Timestamp.today(),
                    "strategy_return": 0.0,
                    "benchmark_return": 0.0,
                    "excess_return": 0.0,
                    "holdings": ", ".join(selected["ticker"].tolist()),
                    "note": "가격 히스토리가 부족해 진단 행만 생성했습니다.",
                }
            ]
        )

    period_days = HORIZON_TO_DAYS.get(rebalance, 21)
    rebalance_dates = unique_dates[::period_days]
    rows = []
    latest_scores = scores.copy()

    for idx, start in enumerate(rebalance_dates):
        end = rebalance_dates[idx + 1] if idx + 1 < len(rebalance_dates) else unique_dates[-1]
        if start >= end:
            continue
        selected = latest_scores.sort_values("total_score", ascending=False).head(top_n)["ticker"].tolist()
        period = price[price["date"].between(start, end)]
        returns = []
        for ticker in selected:
            ticker_prices = period[period["ticker"].eq(ticker)].sort_values("date")
            if len(ticker_prices) < 2:
                continue
            ret = ticker_prices.iloc[-1]["close"] / ticker_prices.iloc[0]["close"] - 1 - transaction_cost
            returns.append(ret)
        strategy_return = sum(returns) / len(returns) if returns else 0.0
        benchmark_return = period["return_1d"].mean() / 100 if "return_1d" in period else 0.0
        rows.append(
            {
                "date": end,
                "strategy_return": strategy_return,
                "benchmark_return": benchmark_return,
                "excess_return": strategy_return - benchmark_return,
                "holdings": ", ".join(selected),
                "note": "",
            }
        )
    return pd.DataFrame(rows)


def horizon_returns(prices: pd.DataFrame, ticker: str) -> dict:
    latest = prices[prices["ticker"].eq(ticker)].sort_values("date").tail(1)
    if latest.empty:
        return {"1W": None, "1M": None, "3M": None, "6M": None}
    row = latest.iloc[0]
    return {
        "1W": None,
        "1M": row.get("return_1m"),
        "3M": row.get("return_3m"),
        "6M": None,
    }
