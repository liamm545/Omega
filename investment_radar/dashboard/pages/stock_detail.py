import pandas as pd
import streamlit as st

from llm.thesis_generator import generate_thesis
from llm.investment_note_generator import generate_investment_note
from scoring.event_score import build_event_candidates


def render_stock_detail(tables: dict, scores: pd.DataFrame) -> None:
    st.title("Stock Detail")
    label_map = {f"{row['name']} ({row['ticker']})": row["ticker"] for _, row in scores.iterrows()}
    selected = st.selectbox("종목", list(label_map.keys()))
    ticker = label_map[selected]
    stock = scores[scores["ticker"].eq(ticker)].iloc[0].to_dict()
    events = build_event_candidates(tables, scores)
    event = events[events["ticker"].eq(ticker)].head(1)
    thesis = generate_thesis(stock, event.iloc[0].to_dict() if not event.empty else None)
    financial = tables["financials"][tables["financials"]["ticker"].eq(ticker)].sort_values(["year", "quarter"]).tail(1)
    valuation = tables["valuation_features"][tables["valuation_features"]["ticker"].eq(ticker)].sort_values("date").tail(1)
    news = tables["news"][tables["news"]["ticker"].eq(ticker)].sort_values("date", ascending=False)
    event_row = event.iloc[0].to_dict() if not event.empty else None
    note = generate_investment_note(
        stock_info=stock,
        financial_summary=financial.to_dict("records")[0] if not financial.empty else None,
        valuation_summary=valuation.to_dict("records")[0] if not valuation.empty else None,
        recent_news=news[["date", "title", "source", "url", "summary"]].head(5).to_dict("records") if not news.empty else None,
        recent_filings=None,
        event_summary=event_row,
        risk_flags=stock.get("risk_flags"),
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("총점", f"{stock['total_score']:.1f}")
    col2.metric("등급", stock["grade"])
    col3.metric("이벤트 점수", f"{stock['event_score']:.1f}")
    st.dataframe(pd.DataFrame([stock]), use_container_width=True, hide_index=True)
    if stock.get("is_value_trap"):
        st.error(f"가치함정 의심: {stock.get('risk_flags')}")
    else:
        st.info(f"가치함정 플래그: {stock.get('risk_flags', 'missing')}")

    st.subheader("투자 노트")
    for key, value in note.items():
        if key in ("최근 뉴스", "최근 공시", "재무 요약"):
            continue
        st.markdown(f"**{key}:** {value}")

    st.subheader("최근 뉴스")
    if news.empty:
        st.write("데이터 없음")
    else:
        st.dataframe(news[["date", "title", "source", "url", "summary"]].head(5), use_container_width=True, hide_index=True)

    st.subheader("최근 공시")
    st.write("DART collector 연동 후 표시됩니다. 현재는 데이터 없음.")

    st.subheader("이벤트 관련성")
    if event.empty:
        st.write("관련 이벤트 없음")
    else:
        st.dataframe(
            event[["event_name", "relation_type", "relation_strength", "event_score", "price_reflection", "earnings_link_probability", "reason"]],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("투자 가설 체크리스트")
    for key, value in thesis.items():
        st.markdown(f"**{key}:** {value}")
