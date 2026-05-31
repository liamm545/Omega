import pandas as pd
import streamlit as st


def render_stock_screener(tables: dict, scores: pd.DataFrame) -> None:
    st.title("Stock Screener")
    st.caption("점수표와 실제 원본 데이터를 함께 확인하는 화면입니다. 높은 점수는 관찰 후보를 좁히는 신호일 뿐입니다.")
    sector = st.multiselect("섹터", sorted(scores["sector"].unique()), default=list(sorted(scores["sector"].unique())))
    min_score = st.slider("최소 총점", 0, 100, 50)
    view = scores[(scores["sector"].isin(sector)) & (scores["total_score"] >= min_score)]
    st.dataframe(
        view[
            [
                "ticker",
                "name",
                "sector",
                "industry_group",
                "cycle_phase",
                "industry_cycle_adjustment",
                "market_cap",
                "valuation_score",
                "quality_score",
                "improvement_score",
                "momentum_score",
                "event_score",
                "risk_penalty",
                "risk_flags",
                "total_score",
                "grade",
                "recommendation_reason",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("선택 후보의 실제 가격 데이터")
    if view.empty:
        st.info("조건에 맞는 종목이 없습니다. 필터를 낮춰보세요.")
        return
    selected = st.selectbox("원본 데이터를 볼 종목", view["ticker"].tolist(), format_func=lambda ticker: f"{ticker} - {view[view['ticker'].eq(ticker)].iloc[0]['name']}")
    if selected:
        prices = tables["daily_prices"][tables["daily_prices"]["ticker"].eq(selected)].sort_values("date", ascending=False)
        financials = tables["financials"][tables["financials"]["ticker"].eq(selected)].sort_values(["year", "quarter"], ascending=False)
        news = tables["news"][tables["news"]["ticker"].eq(selected)].sort_values("date", ascending=False)
        tab1, tab2, tab3 = st.tabs(["가격", "재무", "뉴스"])
        with tab1:
            st.dataframe(prices.head(60), use_container_width=True, hide_index=True)
        with tab2:
            st.dataframe(financials.head(12), use_container_width=True, hide_index=True)
        with tab3:
            st.dataframe(news.head(20), use_container_width=True, hide_index=True)
