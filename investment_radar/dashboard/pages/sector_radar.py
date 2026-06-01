import json

import pandas as pd
import plotly.express as px
import streamlit as st

from sector_intelligence.sector_analyzer import build_sector_analysis
from sector_intelligence.sector_thesis_generator import generate_sector_thesis


def render_sector_radar(tables: dict, scores: pd.DataFrame) -> None:
    st.title("Sector Radar")
    st.caption("섹터별 KPI, 뉴스/공시, 가격 모멘텀, 이벤트 반영도를 종합해 산업 사이클을 판단합니다.")

    analysis = build_sector_analysis(tables, scores)
    if analysis.empty:
        st.warning("섹터 분석 데이터가 없습니다.")
        return

    st.plotly_chart(px.scatter(analysis, x="confidence", y="sector_score", size="sector_score", color="cycle_stage", hover_name="sector"), use_container_width=True)
    st.dataframe(
        analysis[["sector", "cycle_stage", "confidence", "sector_score", "summary"]],
        hide_index=True,
        use_container_width=True,
    )

    for _, row in analysis.iterrows():
        thesis = generate_sector_thesis(row.to_dict())
        with st.expander(f"{row['sector']} 상세 분석"):
            col1, col2, col3 = st.columns(3)
            col1.metric("국면", row["cycle_stage"])
            col2.metric("확신도", f"{row['confidence']:.2f}")
            col3.metric("섹터 점수", f"{row['sector_score']:.1f}")
            st.markdown(f"**요약:** {row['summary']}")
            st.markdown("**투자 가설**")
            for key, value in thesis.items():
                st.markdown(f"- **{key}:** {value}")
            st.markdown("**핵심 KPI 상태**")
            st.dataframe(pd.DataFrame(_as_list(row.get("key_kpis_json"))), hide_index=True, use_container_width=True)
            st.markdown("**리스크 / 체크포인트**")
            st.write(_as_list(row.get("risk_factors_json")) or ["missing"])
            st.write(_as_list(row.get("watch_points_json")) or ["missing"])


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            return [value]
    return []
