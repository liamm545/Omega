import pandas as pd
import streamlit as st

from scoring.event_score import build_event_candidates


def render_event_radar(tables: dict, scores: pd.DataFrame) -> None:
    st.title("Event Radar")
    st.caption("뉴스/공시/이벤트가 실제 실적, 수주, CAPEX로 이어질 가능성을 점검하는 화면입니다.")

    events = tables["events"]
    candidates = build_event_candidates(tables, scores)

    st.subheader("오늘 감지된 주요 이벤트")
    if events.empty:
        st.warning("이벤트 데이터가 없습니다. 현재는 샘플 이벤트 또는 향후 뉴스/공시 기반 이벤트 탐지 결과가 들어오는 영역입니다.")
    for _, event in events.iterrows():
        with st.container(border=True):
            st.markdown(f"### {event['event_name']}")
            st.markdown(f"**관련 인물:** {event['related_person'] or 'missing'}")
            st.markdown(f"**관련 기업:** {event['related_company'] or 'missing'}")
            st.markdown(f"**관련 섹터:** {event['related_sectors']}")
            st.markdown(f"**신뢰도:** {event['confidence_score']:.0f}/100")
            st.write(event["description"])

    news = tables["news"].sort_values("date", ascending=False)
    with st.expander("이벤트 판단에 참고한 최근 뉴스 원본", expanded=False):
        if news.empty:
            st.info("뉴스 원본 데이터가 없습니다. NAVER 뉴스 업데이트가 성공해야 실제 뉴스가 표시됩니다.")
        else:
            st.dataframe(news[["date", "ticker", "title", "source", "url", "summary", "keywords", "event_type"]].head(50), use_container_width=True, hide_index=True)

    st.subheader("이벤트별 관련 종목")
    view = candidates[
        [
            "event_name",
            "ticker",
            "name",
            "sector",
            "relation_type",
            "relation_strength",
            "event_score",
            "price_reflection",
            "secondary_candidate",
            "overheat_risk",
            "earnings_link_probability",
            "reason",
            "grade",
        ]
    ].rename(
        columns={
            "event_name": "이벤트",
            "ticker": "티커",
            "name": "종목",
            "sector": "섹터",
            "relation_type": "관련성 등급",
            "relation_strength": "관련 강도",
            "event_score": "이벤트 점수",
            "price_reflection": "주가 반영 정도",
            "secondary_candidate": "덜 오른 2차 후보",
            "overheat_risk": "단기 과열 위험",
            "earnings_link_probability": "중장기 실적 연결 가능성",
            "reason": "근거",
            "grade": "종합 등급",
        }
    )
    st.dataframe(view, use_container_width=True, hide_index=True)

    st.subheader("덜 오른 2차 수혜 후보")
    secondary = candidates[candidates["secondary_candidate"]]
    if secondary.empty:
        st.info("현재 샘플 데이터에서는 조건에 맞는 2차 후보가 없습니다.")
    else:
        st.dataframe(
            secondary[["ticker", "name", "sector", "relation_type", "return_1m", "event_score", "reason"]],
            use_container_width=True,
            hide_index=True,
        )

    st.warning("본 화면은 매수/매도 판단이 아니라 리서치 후보 압축용입니다. 공식 공시와 원문 출처를 반드시 확인하세요.")
