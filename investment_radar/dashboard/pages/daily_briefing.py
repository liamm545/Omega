import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.pages.macro_dashboard import render_industry_insights
from llm.thesis_generator import generate_thesis
from scoring.event_score import build_event_candidates


def render_daily_briefing(tables: dict, scores: pd.DataFrame) -> None:
    st.title("Daily Briefing")
    st.caption("산업 사이클, 가격, 재무, 뉴스, 이벤트를 결합해 오늘 확인할 투자 가설을 압축합니다.")

    prices = tables["daily_prices"].sort_values("date").groupby("ticker").tail(1)
    stocks = tables["stocks"]
    latest = scores.merge(prices[["ticker", "return_1d", "return_1m", "return_3m"]], on="ticker", how="left")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("분석 종목", len(scores))
    col2.metric("평균 총점", f"{scores['total_score'].mean():.1f}")
    col3.metric("강한 섹터", latest.groupby("sector")["momentum_score"].mean().idxmax())
    col4.metric("이벤트 후보", int((scores["event_score"] > 0).sum()))

    st.subheader("오늘 시장 요약")
    latest_date = prices["date"].max() if not prices.empty else "missing"
    st.write(f"현재 점수 계산에 사용된 최신 가격 기준일은 **{latest_date}**입니다.")
    render_industry_insights(tables)

    st.subheader("강한 섹터 TOP 5")
    sector = (
        latest.groupby("sector", as_index=False)
        .agg(avg_total=("total_score", "mean"), avg_momentum=("momentum_score", "mean"), count=("ticker", "count"))
        .sort_values("avg_total", ascending=False)
        .head(5)
    )
    st.plotly_chart(px.bar(sector, x="sector", y="avg_total", color="avg_momentum"), use_container_width=True)
    st.dataframe(sector, use_container_width=True, hide_index=True)

    st.subheader("저평가 리서치 후보 TOP 20")
    undervalued = scores.sort_values(["valuation_score", "total_score"], ascending=False).head(20)
    st.dataframe(
        undervalued[["ticker", "name", "sector", "cycle_phase", "industry_cycle_adjustment", "valuation_score", "quality_score", "total_score", "grade", "recommendation_reason"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("이벤트 수혜 후보 TOP 20")
    event_candidates = build_event_candidates(tables, scores).head(20)
    st.dataframe(
        event_candidates[
            [
                "event_name",
                "ticker",
                "name",
                "relation_type",
                "relation_strength",
                "event_score",
                "price_reflection",
                "overheat_risk",
                "earnings_link_probability",
                "reason",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("관심종목 뉴스/공시 알림")
    news = tables["news"].merge(stocks[["ticker", "name"]], on="ticker", how="left")
    if news.empty:
        st.warning("뉴스 데이터가 없습니다. NAVER_CLIENT_ID/NAVER_CLIENT_SECRET 설정 후 사이드바의 NAVER 뉴스 업데이트를 실행하세요.")
    else:
        st.dataframe(news[["date", "name", "title", "source", "url", "summary"]], use_container_width=True, hide_index=True)

    st.subheader("리스크 경고 종목")
    risk = latest.sort_values("risk_penalty", ascending=False).head(10)
    st.dataframe(
        risk[["ticker", "name", "sector", "return_1m", "risk_penalty", "total_score", "grade"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("오늘 확인해야 할 질문")
    questions = [
        "산업 KPI가 3개월 이상 같은 방향으로 유지되는가?",
        "현재 산업 국면이 성장인지, 과열인지, 정점인지 구분했는가?",
        "이벤트가 공식 공시, MOU, 계약, CAPEX 중 어느 단계까지 확인되었는가?",
        "최근 1개월 상승률이 이미 기대감을 충분히 반영했는가?",
        "저평가 점수가 높은 종목이 산업 침체기에 있어 value trap이 아닌가?",
    ]
    for question in questions:
        st.markdown(f"- {question}")

    st.subheader("종목 카드 예시")
    top = event_candidates.iloc[0].to_dict() if not event_candidates.empty else {}
    thesis = generate_thesis(top, top)
    with st.container(border=True):
        st.markdown(f"**종목명:** {top.get('name', 'missing')}")
        st.markdown(f"**총점:** {top.get('total_score', 'missing'):.1f}")
        st.markdown(f"**등급:** {top.get('grade', 'missing')}")
        for key, value in thesis.items():
            st.markdown(f"**{key}:** {value}")
