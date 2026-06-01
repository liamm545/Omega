from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.pages.backtest import render_backtest
from dashboard.pages.daily_briefing import render_daily_briefing
from dashboard.pages.event_radar import render_event_radar
from dashboard.pages.macro_dashboard import render_macro_dashboard
from dashboard.pages.sector_radar import render_sector_radar
from dashboard.pages.stock_detail import render_stock_detail
from dashboard.pages.stock_screener import render_stock_screener
from dashboard.pages.watchlist import render_watchlist
from data_collectors.update_pipeline import (
    update_dart_corp_codes,
    update_dart_financials,
    update_industry_kpis_from_news,
    update_macro_indicators,
    update_naver_news,
    update_prices_first_pipeline,
    update_research_intelligence,
)
from database.db import get_connection, initialize_database, load_table
from scoring.total_score import calculate_all_scores
from utils.env import get_env, get_first_env


ROOT = Path(__file__).parent
DB_PATH = Path(get_env("INVESTMENT_RADAR_DB_PATH", str(ROOT / "investment_radar.sqlite")))


st.set_page_config(
    page_title="Investment Radar",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def initialize_app_database():
    initialize_database(DB_PATH)


def boot_database():
    initialize_app_database()
    return get_connection(DB_PATH)


@st.cache_data(ttl=60)
def load_scored_data(_db_version: int = 1):
    conn = boot_database()
    try:
        tables = {
            "stocks": load_table(conn, "stocks"),
            "daily_prices": load_table(conn, "daily_prices"),
            "financials": load_table(conn, "financials"),
            "valuation_features": load_table(conn, "valuation_features"),
            "news": load_table(conn, "news"),
            "events": load_table(conn, "events"),
            "event_stock_map": load_table(conn, "event_stock_map"),
            "macro_indicators": load_table(conn, "macro_indicators"),
            "industry_kpis": load_table(conn, "industry_kpis"),
            "industry_kpi_evidence": load_table(conn, "industry_kpi_evidence"),
            "industry_cycle_signals": load_table(conn, "industry_cycle_signals"),
            "sector_analysis": load_table(conn, "sector_analysis"),
            "event_impacts": load_table(conn, "event_impacts"),
            "market_pricing": load_table(conn, "market_pricing"),
            "daily_briefings": load_table(conn, "daily_briefings"),
            "filings": load_table(conn, "filings"),
        }
        scores = calculate_all_scores(tables)
        return tables, scores
    finally:
        conn.close()


def load_update_logs() -> pd.DataFrame:
    conn = boot_database()
    try:
        return load_table(conn, "update_logs").sort_values("created_at", ascending=False)
    except Exception:
        return pd.DataFrame(columns=["created_at", "source", "status", "rows", "message"])
    finally:
        conn.close()


def render_data_status(tables: dict) -> None:
    prices = tables["daily_prices"]
    stocks = tables["stocks"]
    financials = tables["financials"]
    news = tables["news"]
    logs = load_update_logs()
    latest_price_date = prices["date"].max() if not prices.empty else "missing"
    latest_news_date = news["date"].max() if not news.empty else "missing"

    with st.expander("데이터 상태", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("종목 수", len(stocks))
        col2.metric("가격 row", len(prices))
        col3.metric("최신 가격일", latest_price_date)
        col4.metric("뉴스 row", len(news))

        if latest_news_date != "missing":
            st.caption(f"최신 뉴스 날짜: {latest_news_date}")

        tab1, tab2, tab3, tab4 = st.tabs(["업데이트 로그", "최근 가격 원본", "재무 원본", "뉴스 원본"])
        with tab1:
            if logs.empty:
                st.info("아직 업데이트 로그가 없습니다. 왼쪽 사이드바에서 업데이트 버튼을 눌러보세요.")
            else:
                st.dataframe(logs.head(30), use_container_width=True, hide_index=True)
        with tab2:
            latest_prices = prices.sort_values(["date", "ticker"], ascending=[False, True]).head(50)
            st.dataframe(latest_prices, use_container_width=True, hide_index=True)
        with tab3:
            st.dataframe(financials.sort_values(["year", "quarter", "ticker"], ascending=[False, False, True]).head(50), use_container_width=True, hide_index=True)
        with tab4:
            st.dataframe(news.sort_values("date", ascending=False).head(50), use_container_width=True, hide_index=True)


def main():
    st.sidebar.title("Investment Radar")
    st.sidebar.caption("AI 투자 리서치 플랫폼")

    with st.sidebar.expander("API 연결 상태", expanded=False):
        api_status = {
            "DART": bool(get_env("DART_API_KEY")),
            "NAVER": bool(get_first_env(["NAVER_CLIENT_ID", "NAVER_SEARCH_CLIENT_ID", "VITE_NAVER_CLIENT_ID"]))
            and bool(get_first_env(["NAVER_CLIENT_SECRET", "NAVER_SEARCH_CLIENT_SECRET", "VITE_NAVER_CLIENT_SECRET"])),
            "KRX": bool(get_env("KRX_API_KEY")),
            "KIS": bool(get_env("KIS_APP_KEY")) and bool(get_env("KIS_APP_SECRET")),
            "OpenAI": bool(get_env("OPENAI_API_KEY")),
        }
        for name, ok in api_status.items():
            st.write(f"{'✅' if ok else '⚠️'} {name}: {'configured' if ok else 'not configured'}")
        if st.button("pykrx 주가 업데이트"):
            with st.spinner("pykrx로 종목/가격/시총 데이터를 업데이트 중입니다..."):
                conn = boot_database()
                result = update_prices_first_pipeline(conn)
                conn.close()
                load_scored_data.clear()
            st.success(f"업데이트 완료: {result}")
        if st.button("매크로 지표 업데이트"):
            with st.spinner("FRED, Frankfurter, Stooq에서 매크로 지표를 업데이트 중입니다..."):
                conn = boot_database()
                result = update_macro_indicators(conn)
                conn.close()
                load_scored_data.clear()
            if result.get("macro_indicators", 0) > 0:
                st.success(f"매크로 업데이트 완료: {result}")
            else:
                st.error(f"매크로 업데이트 실패: {result}")
        if st.button("산업 KPI 업데이트"):
            with st.spinner("NAVER 뉴스에서 산업 KPI와 출처 링크를 추출하는 중입니다..."):
                conn = boot_database()
                result = update_industry_kpis_from_news(conn)
                conn.close()
                load_scored_data.clear()
            if result.get("industry_kpis", 0) > 0:
                st.success(f"산업 KPI 업데이트 완료: {result}")
            else:
                st.error(f"산업 KPI 업데이트 실패: {result}")
        if st.button("DART corp_code 매핑 업데이트"):
            with st.spinner("DART corp_code 매핑을 업데이트 중입니다..."):
                conn = boot_database()
                result = update_dart_corp_codes(conn)
                conn.close()
                load_scored_data.clear()
            st.success(f"DART 업데이트 완료: {result}")
        if st.button("DART 재무제표 업데이트"):
            with st.spinner("DART 재무제표를 업데이트 중입니다..."):
                conn = boot_database()
                result = update_dart_financials(conn)
                conn.close()
                load_scored_data.clear()
            st.success(f"DART 재무제표 업데이트 완료: {result}")
        if st.button("NAVER 뉴스 업데이트"):
            with st.spinner("네이버 뉴스 데이터를 업데이트 중입니다..."):
                conn = boot_database()
                result = update_naver_news(conn)
                conn.close()
                load_scored_data.clear()
            if result.get("news", 0) > 0:
                st.success(f"뉴스 업데이트 완료: {result}")
            else:
                st.error(f"뉴스 업데이트 실패 또는 결과 없음: {result}")
        if st.button("리서치 분석 업데이트"):
            with st.spinner("섹터 사이클, 이벤트 영향, 주가 반영도, Daily Briefing을 계산 중입니다..."):
                conn = boot_database()
                result = update_research_intelligence(conn)
                conn.close()
                load_scored_data.clear()
            st.success(f"리서치 분석 업데이트 완료: {result}")

    page = st.sidebar.radio(
        "화면",
        [
            "Daily Briefing",
            "Event Radar",
            "Stock Screener",
            "Sector Radar",
            "Stock Detail",
            "Backtest",
            "Watchlist",
        ],
    )

    tables, scores = load_scored_data()
    if page != "Daily Briefing":
        render_macro_dashboard(tables)
    render_data_status(tables)

    if page == "Daily Briefing":
        render_daily_briefing(tables, scores)
    elif page == "Event Radar":
        render_event_radar(tables, scores)
    elif page == "Stock Screener":
        render_stock_screener(tables, scores)
    elif page == "Sector Radar":
        render_sector_radar(tables, scores)
    elif page == "Stock Detail":
        render_stock_detail(tables, scores)
    elif page == "Backtest":
        render_backtest(tables, scores)
    elif page == "Watchlist":
        render_watchlist(tables, scores)


if __name__ == "__main__":
    main()
