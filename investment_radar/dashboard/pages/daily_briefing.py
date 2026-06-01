import json

import pandas as pd
import plotly.express as px
import streamlit as st

from event_impact.event_impact_analyzer import analyze_event_impacts
from industry_kpi.kpi_signal import latest_kpi_status
from llm.deep_research_analyst import generate_deep_daily_briefing
from scoring.event_score import build_event_candidates
from sector_intelligence.sector_analyzer import build_sector_analysis


SNAPSHOT_INDICATORS = ["USD_KRW", "KOSPI", "KOSDAQ", "SP500", "NASDAQ", "US10Y", "WTI", "NATGAS", "GOLD", "SILVER", "COPPER", "SOX"]
SNAPSHOT_KPIS = [
    ("반도체", "메모리 수출 증가율"),
    ("반도체", "D램 수출 증가율"),
    ("반도체", "낸드 수출 증가율"),
    ("반도체", "HBM 성장률"),
]


def render_daily_briefing(tables: dict, scores: pd.DataFrame) -> None:
    st.title("Daily Briefing")
    st.caption("시장 지표, 산업 KPI, 뉴스/공시, 주가 반영도를 함께 읽어 오늘의 리서치 후보와 검증 질문을 압축합니다.")

    sector_analysis = build_sector_analysis(tables, scores)
    event_impacts, market_pricing, second_order = analyze_event_impacts(tables)
    briefing = _cached_deep_briefing(_table_records(tables), _score_records(scores))

    _render_market_snapshot(tables, scores)
    _render_core_summary(briefing)
    _render_sector_cycles(sector_analysis)
    _render_major_events(event_impacts)
    _render_direct_beneficiaries(tables, scores)
    _render_second_order(second_order)
    _render_overheated(market_pricing, scores)
    _render_value_plus_cycle(scores)
    _render_risk_alerts(briefing)
    _render_questions(briefing)
    _render_ai_conclusion(briefing)


def _render_market_snapshot(tables: dict, scores: pd.DataFrame) -> None:
    st.subheader("1. Market Snapshot")
    macro = tables.get("macro_indicators", pd.DataFrame())
    latest_macro = _latest(macro, ["indicator"]) if not macro.empty else pd.DataFrame()
    lookup = latest_macro.set_index("indicator").to_dict("index") if not latest_macro.empty else {}
    columns = st.columns(4)
    for idx, indicator in enumerate(SNAPSHOT_INDICATORS):
        item = lookup.get(indicator)
        label = item.get("name") if item else indicator
        value = _format_value(item.get("value"), item.get("unit")) if item else "missing"
        delta = item.get("change_1d") if item else None
        columns[idx % 4].metric(label, value, delta=f"{delta:g}%" if pd.notna(delta) else None)

    strong, weak = _sector_strength(scores)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**전일 강세 섹터 TOP 5**")
        st.dataframe(strong, hide_index=True, use_container_width=True)
    with col2:
        st.markdown("**전일 약세 섹터 TOP 5**")
        st.dataframe(weak, hide_index=True, use_container_width=True)

    kpis = tables.get("industry_kpis", pd.DataFrame())
    kpi_rows = []
    for sector, kpi_name in SNAPSHOT_KPIS:
        status_rows = latest_kpi_status(kpis, sector)
        matched = next((row for row in status_rows if row.get("kpi_name") == kpi_name), None)
        kpi_rows.append(
            {
                "sector": sector,
                "kpi": kpi_name,
                "value": _kpi_value(matched),
                "status": (matched or {}).get("status", "missing"),
                "source_url": (matched or {}).get("source_url", ""),
            }
        )
    st.dataframe(kpi_rows, hide_index=True, use_container_width=True, column_config={"source_url": st.column_config.LinkColumn("출처")})


def _render_core_summary(briefing: dict) -> None:
    st.subheader("2. 오늘의 핵심 요약")
    st.info(briefing.get("market_summary", "missing"))


def _render_sector_cycles(sector_analysis: pd.DataFrame) -> None:
    st.subheader("3. 섹터별 사이클 분석")
    if sector_analysis.empty:
        st.warning("섹터 분석 데이터가 없습니다.")
        return
    top = sector_analysis.head(12)
    st.plotly_chart(px.bar(top, x="sector", y="sector_score", color="cycle_stage"), use_container_width=True)
    for _, row in top.iterrows():
        with st.expander(f"{row['sector']} | {row['cycle_stage']} | score {row['sector_score']}"):
            st.write(row["summary"])
            st.markdown("**긍정 근거**")
            st.write(_as_list(row.get("positive_signals_json")) or ["missing"])
            st.markdown("**부정/주의 신호**")
            st.write(_as_list(row.get("negative_signals_json")) or ["missing"])
            st.markdown("**핵심 KPI**")
            st.dataframe(pd.DataFrame(_as_list(row.get("key_kpis_json"))), hide_index=True, use_container_width=True)
            st.markdown("**체크포인트**")
            st.write(_as_list(row.get("watch_points_json")) or ["missing"])


def _render_major_events(event_impacts: pd.DataFrame) -> None:
    st.subheader("4. 오늘의 주요 이벤트")
    if event_impacts.empty:
        st.info("분석 가능한 이벤트가 없습니다. NAVER 뉴스 업데이트 후 더 풍부해집니다.")
        return
    show = event_impacts[["date", "event_name", "event_type", "impact_timeframe", "earnings_link_probability", "market_pricing_level", "investment_implication"]].head(10)
    show = show.rename(
        columns={
            "date": "날짜",
            "event_name": "이벤트",
            "event_type": "이벤트 유형",
            "impact_timeframe": "영향 기간",
            "earnings_link_probability": "실적 연결 가능성",
            "market_pricing_level": "주가 반영도",
            "investment_implication": "투자 해석",
        }
    )
    st.dataframe(show, hide_index=True, use_container_width=True)
    for _, row in event_impacts.head(5).iterrows():
        with st.expander(row["event_name"]):
            st.markdown(f"**분석:** {row.get('investment_implication', 'missing')}")
            negative = _as_list(row.get("negative_impact_companies_json"))
            if negative:
                st.markdown(f"**부정 영향:** {', '.join(negative)}")
            else:
                st.markdown(f"**직접 수혜:** {', '.join(_as_list(row.get('direct_beneficiaries_json'))) or 'missing'}")
                st.markdown(f"**2차 수혜:** {', '.join(_as_list(row.get('second_order_beneficiaries_json'))) or 'missing'}")
            st.markdown(f"**확인 질문:** {', '.join(_as_list(row.get('key_questions_json'))) or 'missing'}")
            for url in _as_list(row.get("source_urls_json")):
                if url:
                    st.link_button("출처 보기", url)


def _render_direct_beneficiaries(tables: dict, scores: pd.DataFrame) -> None:
    st.subheader("5. 직접 수혜주")
    candidates = build_event_candidates(tables, scores)
    if candidates.empty:
        st.info("직접 수혜 후보가 없습니다.")
        return
    direct = candidates[candidates["relation_type"].eq("DIRECT")].drop_duplicates(["ticker", "event_name"]).head(20)
    columns = ["event_name", "ticker", "name", "event_score", "price_reflection", "overheat_risk", "earnings_link_probability", "reason"]
    view = direct[[column for column in columns if column in direct.columns]].rename(
        columns={
            "event_name": "이벤트",
            "ticker": "티커",
            "name": "종목명",
            "event_score": "이벤트 점수",
            "price_reflection": "주가 반영 상태",
            "overheat_risk": "단기 과열 위험",
            "earnings_link_probability": "실적 연결 판단",
            "reason": "근거",
        }
    )
    st.dataframe(view, hide_index=True, use_container_width=True)


def _render_second_order(second_order: list[dict]) -> None:
    st.subheader("6. 2차 수혜 후보")
    if not second_order:
        st.info("2차 수혜 후보가 없습니다.")
        return
    shown = 0
    for item in second_order:
        if not item.get("candidate_sectors") and not item.get("candidate_stocks"):
            continue
        shown += 1
        with st.expander(item.get("event", "missing")):
            st.markdown(f"**왜 중요한가:** {item.get('why_it_matters', 'missing')}")
            st.markdown(f"**시장이 놓칠 수 있는 부분:** {item.get('what_market_may_be_missing', 'missing')}")
            st.markdown(f"**후보 섹터:** {', '.join(item.get('candidate_sectors', [])) or 'missing'}")
            st.dataframe(pd.DataFrame(item.get("candidate_stocks", [])), hide_index=True, use_container_width=True)
        if shown >= 6:
            break
    if shown == 0:
        st.info("현재 뉴스에서 논리적 연결고리가 있는 2차 수혜 후보를 찾지 못했습니다.")


def _render_overheated(market_pricing: pd.DataFrame, scores: pd.DataFrame) -> None:
    st.subheader("7. 이미 과열된 종목")
    if market_pricing.empty:
        st.info("이벤트 발생일 기준 가격 반응 데이터가 부족합니다.")
        return
    hot = market_pricing[market_pricing["pricing_level"].isin(["HIGH", "EXTREME"])].drop_duplicates(["ticker", "event_name"])
    if hot.empty:
        st.success("현재 이벤트 기준 HIGH/EXTREME 과열 신호는 없습니다.")
        return
    enriched = hot.merge(scores[["ticker", "name", "sector", "total_score"]], on="ticker", how="left")
    view = enriched[["ticker", "name", "sector", "event_name", "price_reaction_1d", "volume_spike", "pricing_level", "interpretation"]].rename(
        columns={
            "ticker": "티커",
            "name": "종목명",
            "sector": "섹터",
            "event_name": "이벤트",
            "price_reaction_1d": "이벤트 당일 반응",
            "volume_spike": "거래대금 증가 배수",
            "pricing_level": "주가 반영도",
            "interpretation": "해석",
        }
    )
    st.dataframe(view, hide_index=True, use_container_width=True)


def _render_value_plus_cycle(scores: pd.DataFrame) -> None:
    st.subheader("8. 저평가 + 산업 개선 후보")
    if scores.empty:
        st.info("스코어 데이터가 없습니다.")
        return
    candidate = scores[
        (scores["valuation_score"] >= scores["valuation_score"].quantile(0.6))
        & (scores["cycle_stage"].isin(["RECOVERY", "EXPANSION", "UNKNOWN"]))
    ].head(20)
    candidate = candidate.assign(
        판단=lambda frame: frame.apply(_value_cycle_reason, axis=1),
    )
    columns = ["ticker", "name", "sector", "intelligence_sector", "cycle_stage", "valuation_score", "sector_cycle_score", "second_order_score", "overheating_penalty", "total_score", "grade", "판단", "recommendation_reason"]
    view = candidate[[column for column in columns if column in candidate.columns]].rename(
        columns={
            "ticker": "티커",
            "name": "종목명",
            "sector": "기존 섹터",
            "intelligence_sector": "분석 섹터",
            "cycle_stage": "산업 국면",
            "valuation_score": "저평가 점수",
            "sector_cycle_score": "산업 개선 점수",
            "second_order_score": "2차 수혜 점수",
            "overheating_penalty": "과열 차감",
            "total_score": "종합 점수",
            "grade": "등급",
            "recommendation_reason": "계산 근거",
        }
    )
    st.dataframe(view, hide_index=True, use_container_width=True)


def _render_risk_alerts(briefing: dict) -> None:
    st.subheader("9. 리스크 경고")
    alerts = briefing.get("risk_alerts") or []
    if not alerts:
        st.info("현재 자동 생성된 리스크 경고가 없습니다.")
        return
    st.dataframe(pd.DataFrame(alerts), hide_index=True, use_container_width=True)


def _render_questions(briefing: dict) -> None:
    st.subheader("10. 오늘 확인해야 할 질문")
    for question in briefing.get("today_key_questions", []) or ["missing"]:
        st.markdown(f"- {question}")


def _render_ai_conclusion(briefing: dict) -> None:
    st.subheader("11. AI 결론")
    st.success(briefing.get("conclusion", "missing"))


@st.cache_data(ttl=1800, show_spinner=False)
def _cached_deep_briefing(table_records: dict, score_records: list[dict]) -> dict:
    tables = {name: pd.DataFrame(records) for name, records in table_records.items()}
    scores = pd.DataFrame(score_records)
    return generate_deep_daily_briefing(tables, scores)


def _table_records(tables: dict) -> dict:
    keep = ["macro_indicators", "industry_kpis", "industry_kpi_evidence", "news", "events", "event_stock_map", "daily_prices", "stocks", "filings"]
    return {name: tables.get(name, pd.DataFrame()).to_dict("records") for name in keep}


def _score_records(scores: pd.DataFrame) -> list[dict]:
    return scores.head(200).to_dict("records") if scores is not None and not scores.empty else []


def _latest(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return frame.sort_values("date").groupby(keys, as_index=False).tail(1) if frame is not None and not frame.empty else pd.DataFrame()


def _sector_strength(scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if scores.empty:
        empty = pd.DataFrame(columns=["sector", "return_1d", "momentum_score"])
        return empty, empty
    sector = scores.groupby("sector", as_index=False).agg(return_1d=("return_1d", "mean"), momentum_score=("momentum_score", "mean"), count=("ticker", "count"))
    return sector.sort_values("return_1d", ascending=False).head(5), sector.sort_values("return_1d").head(5)


def _format_value(value, unit) -> str:
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return "missing"
    return f"{value:,.2f} {unit or ''}".strip()


def _kpi_value(row: dict | None) -> str:
    if not row or row.get("status") == "missing":
        return "missing"
    return _format_value(row.get("value"), row.get("unit"))


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            return [value] if value else []
    return [value]


def _value_cycle_reason(row: pd.Series) -> str:
    notes = []
    if row.get("valuation_score", 0) >= 70:
        notes.append("밸류에이션 매력")
    if row.get("cycle_stage") in ["RECOVERY", "EXPANSION"]:
        notes.append("산업 개선 확인")
    elif row.get("cycle_stage") == "UNKNOWN":
        notes.append("산업 KPI 확인 필요")
    if row.get("overheating_penalty", 0) > 0:
        notes.append("단기 과열 주의")
    if row.get("second_order_score", 0) >= 50:
        notes.append("2차 수혜 가능성")
    return " / ".join(notes) if notes else "근거 부족"
