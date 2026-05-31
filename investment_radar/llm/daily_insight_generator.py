import json

import pandas as pd

from utils.env import get_env


def generate_daily_ai_insight(tables: dict, scores: pd.DataFrame) -> dict:
    context = _build_context(tables, scores)
    if get_env("OPENAI_API_KEY"):
        generated = _try_openai_insight(context)
        if generated:
            return generated
    return _fallback_insight(context)


def _build_context(tables: dict, scores: pd.DataFrame) -> dict:
    macro = tables.get("macro_indicators", pd.DataFrame())
    kpis = tables.get("industry_kpis", pd.DataFrame())
    evidence = tables.get("industry_kpi_evidence", pd.DataFrame())
    news = tables.get("news", pd.DataFrame())
    top_scores = scores.head(20) if scores is not None and not scores.empty else pd.DataFrame()
    return {
        "macro": _records(_latest_by(macro, ["indicator"]), ["date", "indicator", "name", "value", "unit", "change_1d", "change_1m", "source"], 20),
        "industry_kpis": _records(_latest_by(kpis, ["industry", "kpi"]), ["date", "industry", "kpi", "value", "unit", "source", "evidence_url"], 30),
        "kpi_evidence": _records(
            _sort_if_column(evidence, "collected_at", ascending=False),
            ["published_at", "industry", "kpi", "value", "unit", "title", "url", "summary", "source"],
            30,
        ),
        "recent_news": _records(news.sort_values("date", ascending=False) if not news.empty else news, ["date", "ticker", "title", "source", "url", "summary"], 20),
        "top_candidates": _records(
            top_scores,
            ["ticker", "name", "sector", "industry_group", "cycle_phase", "total_score", "grade", "recommendation_reason"],
            20,
        ),
    }


def _try_openai_insight(context: dict) -> dict:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=get_env("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=get_env("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
        )
        payload = json.loads(response.choices[0].message.content)
        return _validate(payload)
    except Exception:
        return {}


def _system_prompt() -> str:
    return (
        "너는 산업 사이클 기반 투자 리서치 애널리스트다. 입력된 macro, industry_kpis, kpi_evidence, news, top_candidates만 근거로 사용한다. "
        "입력에 없는 숫자나 사실을 만들지 마라. 매수/매도 추천 금지. '관찰 후보', '리서치 후보'라고 표현한다. "
        "뉴스 요약이 아니라 산업 흐름, 근거, 반대 시나리오, 체크포인트, 후보군 압축을 작성한다. "
        "반드시 JSON object로 답한다. 키: 오늘의 결론, 강한 산업, 약한 신호, 핵심 근거, 관찰 후보, 리스크, 확인할 질문, 출처."
    )


def _validate(payload: dict) -> dict:
    keys = ["오늘의 결론", "강한 산업", "약한 신호", "핵심 근거", "관찰 후보", "리스크", "확인할 질문", "출처"]
    return {key: payload.get(key, "missing") for key in keys}


def _fallback_insight(context: dict) -> dict:
    kpis = context.get("industry_kpis", [])
    candidates = context.get("top_candidates", [])
    evidence = context.get("kpi_evidence", [])
    strong = sorted(kpis, key=lambda item: float(item.get("value") or 0), reverse=True)[:5]
    return {
        "오늘의 결론": "LLM 키가 없거나 호출에 실패했습니다. 수집된 KPI와 후보군을 기준으로 추가 검토가 필요합니다.",
        "강한 산업": ", ".join(sorted({item.get("industry", "") for item in strong if item.get("industry")})) or "missing",
        "약한 신호": "missing",
        "핵심 근거": " | ".join([f"{item.get('industry')} {item.get('kpi')}={item.get('value')}{item.get('unit', '')}" for item in strong]) or "missing",
        "관찰 후보": ", ".join([f"{item.get('name')}({item.get('ticker')})" for item in candidates[:8]]) or "missing",
        "리스크": "KPI가 뉴스 추출값인 경우 공식 통계/공시로 교차검증 필요",
        "확인할 질문": "뉴스 추출 KPI가 공식 데이터와 일치하는가? 가격에 이미 반영되었는가?",
        "출처": ", ".join([item.get("url", "") for item in evidence[:5] if item.get("url")]) or "missing",
    }


def _latest_by(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    return frame.sort_values("date").groupby(keys, as_index=False).tail(1)


def _sort_if_column(frame: pd.DataFrame, column: str, ascending: bool = True) -> pd.DataFrame:
    if frame is None or frame.empty or column not in frame.columns:
        return frame if frame is not None else pd.DataFrame()
    return frame.sort_values(column, ascending=ascending)


def _records(frame: pd.DataFrame, columns: list[str], limit: int) -> list[dict]:
    if frame is None or frame.empty:
        return []
    usable = [column for column in columns if column in frame.columns]
    return frame[usable].head(limit).to_dict("records")
