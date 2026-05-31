import pandas as pd
import plotly.express as px
import streamlit as st

from backtesting.performance_metrics import summarize_performance
from backtesting.portfolio_backtester import run_score_top_n_backtest


def render_backtest(tables: dict, scores: pd.DataFrame) -> None:
    st.title("Backtest")
    st.caption("자동매매가 아니라 리서치 팩터 검증용 백테스트입니다. 샘플 데이터는 히스토리가 짧습니다.")

    col1, col2, col3 = st.columns(3)
    top_n = col1.slider("상위 N개", 1, 20, 5)
    rebalance = col2.selectbox("리밸런싱 주기", ["1W", "1M", "3M", "6M"], index=1)
    transaction_cost = col3.number_input("거래비용", min_value=0.0, max_value=0.02, value=0.001, step=0.0005, format="%.4f")

    dates = pd.to_datetime(tables["daily_prices"]["date"])
    start_date = st.date_input("시작일", dates.min().date())
    end_date = st.date_input("종료일", dates.max().date())
    prices = tables["daily_prices"].copy()
    prices["date"] = pd.to_datetime(prices["date"])
    prices = prices[prices["date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))]

    result = run_score_top_n_backtest(scores, prices, top_n=top_n, rebalance=rebalance, transaction_cost=transaction_cost)
    metrics = summarize_performance(result)

    if result.empty:
        st.warning("백테스트에 필요한 데이터가 부족합니다.")
        return

    result = result.copy()
    result["strategy_equity"] = (1 + result["strategy_return"].fillna(0)).cumprod()
    result["benchmark_equity"] = (1 + result["benchmark_return"].fillna(0)).cumprod()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("누적수익률", f"{metrics.get('cumulative_return', 0):.2%}")
    m2.metric("초과수익", f"{metrics.get('excess_return', 0):.2%}")
    m3.metric("Sharpe", f"{metrics.get('sharpe_ratio', 0):.2f}")
    m4.metric("MDD", f"{metrics.get('mdd', 0):.2%}")

    chart = result.melt(id_vars=["date"], value_vars=["strategy_equity", "benchmark_equity"], var_name="series", value_name="equity")
    st.plotly_chart(px.line(chart, x="date", y="equity", color="series"), use_container_width=True)

    monthly = result.copy()
    monthly["month"] = pd.to_datetime(monthly["date"]).dt.to_period("M").astype(str)
    monthly_table = monthly.groupby("month", as_index=False)[["strategy_return", "benchmark_return", "excess_return"]].sum()
    st.subheader("월별 수익률")
    st.dataframe(monthly_table, use_container_width=True, hide_index=True)

    st.subheader("리밸런싱 내역")
    st.dataframe(result, use_container_width=True, hide_index=True)
