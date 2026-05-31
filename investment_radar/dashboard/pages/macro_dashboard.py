import pandas as pd
import streamlit as st

from industry_intelligence.cycle_detector import detect_industry_cycles
from industry_intelligence.thesis_engine import build_industry_theses


MACRO_ORDER = ["USD_KRW", "KOSPI", "KOSDAQ", "SP500", "NASDAQ", "US10Y", "WTI", "NATGAS", "GOLD", "SILVER", "COPPER", "SOX"]


def render_macro_dashboard(tables: dict) -> None:
    macro = tables.get("macro_indicators", pd.DataFrame())
    kpis = tables.get("industry_kpis", pd.DataFrame())
    evidence = tables.get("industry_kpi_evidence", pd.DataFrame())
    cycles = detect_industry_cycles(kpis)

    st.subheader("Macro Dashboard")
    if macro.empty:
        st.info("매크로 데이터가 없습니다. 왼쪽 사이드바에서 `매크로 지표 업데이트`를 실행하세요.")
    else:
        latest_macro = macro.sort_values("date").groupby("indicator", as_index=False).tail(1)
        latest_macro["sort_order"] = latest_macro["indicator"].apply(lambda item: MACRO_ORDER.index(item) if item in MACRO_ORDER else 999)
        latest_macro = latest_macro.sort_values("sort_order")
        columns = st.columns(4)
        for idx, row in enumerate(latest_macro.to_dict("records")):
            delta = row.get("change_1d")
            columns[idx % 4].metric(
                row.get("name") or row.get("indicator"),
                _format_value(row.get("value"), row.get("unit")),
                delta=f"{delta:g}%" if pd.notna(delta) else None,
            )

    st.subheader("Industry KPI")
    _render_evidence_board(evidence)
    if kpis.empty:
        st.info("산업 KPI 데이터가 없습니다. D램/NAND/HBM 같은 산업 KPI는 출처가 확정된 collector 또는 수동 업로드 데이터가 들어오기 전까지 표시하지 않습니다.")
        return

    latest_kpis = kpis.sort_values("date").groupby(["industry", "kpi"], as_index=False).tail(1)
    focus = latest_kpis[latest_kpis["industry"].isin(["반도체", "AI 인프라"])]
    st.dataframe(
        focus[["date", "industry", "kpi", "value", "unit", "change_1m", "change_3m", "source", "evidence_url"]].sort_values(["industry", "kpi"]),
        use_container_width=True,
        hide_index=True,
        column_config={"evidence_url": st.column_config.LinkColumn("출처")},
    )

    if not cycles.empty:
        st.subheader("Industry Cycle")
        st.dataframe(
            cycles[["industry", "cycle_phase", "cycle_score", "confidence", "positive_evidence", "checkpoints", "beneficiaries", "risks"]],
            use_container_width=True,
            hide_index=True,
        )


def render_industry_insights(tables: dict) -> None:
    kpis = tables.get("industry_kpis", pd.DataFrame())
    cycles = detect_industry_cycles(kpis)
    if cycles.empty:
        return
    theses = _cached_build_industry_theses(
        cycles.to_dict("records"),
        kpis.to_dict("records"),
        tables.get("news", pd.DataFrame()).to_dict("records"),
        tables.get("filings", pd.DataFrame()).to_dict("records"),
    )
    thesis_map = {row["industry"]: row["thesis"] for _, row in theses.iterrows()}

    st.subheader("오늘의 산업 인사이트")
    for _, row in cycles.sort_values("cycle_score", ascending=False).head(5).iterrows():
        thesis = thesis_map.get(row["industry"], {})
        with st.container(border=True):
            col1, col2, col3 = st.columns([1.2, 1, 1])
            col1.markdown(f"### {row['industry']}")
            col2.metric("산업 국면", row["cycle_phase"])
            col3.metric("사이클 점수", f"{row['cycle_score']:.1f}")
            st.markdown(f"**핵심 근거:** {thesis.get('핵심 근거', row['positive_evidence'])}")
            st.markdown(f"**반대 시나리오:** {thesis.get('반대 시나리오', row['negative_evidence'])}")
            st.markdown(f"**3~6개월 체크포인트:** {thesis.get('향후 3~6개월 체크포인트', row['checkpoints'])}")
            st.markdown(f"**수혜 후보:** {thesis.get('수혜 업종', row['beneficiaries'])}")
            st.markdown(f"**놓치기 쉬운 부분:** {thesis.get('투자자가 놓치기 쉬운 부분', 'missing')}")
            _render_industry_sources(tables, row["industry"])


def _format_value(value, unit: str) -> str:
    if pd.isna(value):
        return "missing"
    if unit == "%":
        return f"{value:g}%"
    return f"{value:,.2f} {unit or ''}".strip()


def _render_industry_sources(tables: dict, industry: str) -> None:
    evidence = tables.get("industry_kpi_evidence", pd.DataFrame())
    if evidence.empty:
        return
    rows = evidence[evidence["industry"].eq(industry)].sort_values("collected_at", ascending=False).head(5)
    if rows.empty:
        return
    st.markdown("**출처:**")
    for _, item in rows.iterrows():
        title = item.get("title") or item.get("url")
        st.markdown(f"- [{title}]({item.get('url')})")


def _render_evidence_board(evidence: pd.DataFrame) -> None:
    with st.expander("KPI Evidence Board", expanded=False):
        if evidence.empty:
            st.info("아직 KPI evidence가 없습니다. 왼쪽 사이드바에서 `산업 KPI 업데이트`를 실행하세요.")
            return
        latest_evidence = evidence.sort_values("collected_at", ascending=False).head(100)
        st.dataframe(
            latest_evidence[["collected_at", "published_at", "industry", "kpi", "value", "unit", "title", "url", "summary", "source"]],
            use_container_width=True,
            hide_index=True,
            column_config={"url": st.column_config.LinkColumn("기사 링크")},
        )


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_build_industry_theses(cycle_records: list[dict], kpi_records: list[dict], news_records: list[dict], filing_records: list[dict]) -> pd.DataFrame:
    return build_industry_theses(
        pd.DataFrame(cycle_records),
        pd.DataFrame(kpi_records),
        pd.DataFrame(news_records),
        pd.DataFrame(filing_records),
    )
