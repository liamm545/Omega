import json

import pandas as pd

from utils.env import get_env


def build_industry_theses(cycle_signals: pd.DataFrame, industry_kpis: pd.DataFrame, news: pd.DataFrame = None, filings: pd.DataFrame = None) -> pd.DataFrame:
    if cycle_signals.empty:
        return pd.DataFrame(columns=["industry", "thesis"])

    rows = []
    for _, signal in cycle_signals.iterrows():
        industry = signal["industry"]
        kpis = industry_kpis[industry_kpis["industry"].eq(industry)] if not industry_kpis.empty else pd.DataFrame()
        context = {
            "industry": industry,
            "cycle_phase": signal.get("cycle_phase"),
            "cycle_score": signal.get("cycle_score"),
            "confidence": signal.get("confidence"),
            "kpis": _records(kpis, ["date", "kpi", "value", "unit", "change_1m", "change_3m", "source", "evidence_url"]),
            "recent_news": _records(news if news is not None else pd.DataFrame(), ["date", "ticker", "title", "source", "url", "summary"])[:5],
            "recent_filings": _records(filings if filings is not None else pd.DataFrame(), ["rcept_dt", "corp_name", "report_nm"])[:5],
        }
        rows.append({"industry": industry, "thesis": generate_industry_thesis(context, signal)})
    return pd.DataFrame(rows)


def generate_industry_thesis(context: dict, signal: dict) -> dict:
    if get_env("OPENAI_API_KEY"):
        generated = _try_openai_thesis(context)
        if generated:
            return generated
    return _rule_based_thesis(context, signal)


def _rule_based_thesis(context: dict, signal: dict) -> dict:
    phase = signal.get("cycle_phase", "missing")
    industry = signal.get("industry", "missing")
    return {
        "현재 산업 국면": phase,
        "핵심 근거": signal.get("positive_evidence", "missing"),
        "반대 시나리오": signal.get("negative_evidence", "명확한 음수 KPI는 아직 확인되지 않음"),
        "향후 3~6개월 체크포인트": signal.get("checkpoints", "missing"),
        "수혜 업종": signal.get("beneficiaries", "missing"),
        "피해 업종": signal.get("risks", "missing"),
        "가장 중요한 KPI": _most_important_kpi(context.get("kpis", [])),
        "투자자가 놓치기 쉬운 부분": _blind_spot(industry, phase),
    }


def _try_openai_thesis(context: dict) -> dict:
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
        return _validate_thesis(payload)
    except Exception:
        return {}


def _system_prompt() -> str:
    return (
        "너는 산업 사이클 분석가다. 입력에 없는 수치를 만들지 마라. "
        "뉴스 요약이 아니라 KPI, 뉴스, 공시, 가격 추세를 근거로 투자 가설을 작성한다. "
        "반드시 JSON object로 답하고 키는 다음과 같다: 현재 산업 국면, 핵심 근거, 반대 시나리오, "
        "향후 3~6개월 체크포인트, 수혜 업종, 피해 업종, 가장 중요한 KPI, 투자자가 놓치기 쉬운 부분."
    )


def _validate_thesis(payload: dict) -> dict:
    keys = ["현재 산업 국면", "핵심 근거", "반대 시나리오", "향후 3~6개월 체크포인트", "수혜 업종", "피해 업종", "가장 중요한 KPI", "투자자가 놓치기 쉬운 부분"]
    return {key: payload.get(key, "missing") for key in keys}


def _records(frame: pd.DataFrame, columns: list[str]) -> list[dict]:
    if frame is None or frame.empty:
        return []
    usable = [column for column in columns if column in frame.columns]
    return frame[usable].head(20).to_dict("records")


def _most_important_kpi(kpis: list[dict]) -> str:
    if not kpis:
        return "missing"
    ranked = sorted(kpis, key=lambda item: abs(float(item.get("change_3m") or item.get("value") or 0)), reverse=True)
    top = ranked[0]
    return f"{top.get('kpi')}: {top.get('value')} {top.get('unit', '')}".strip()


def _blind_spot(industry: str, phase: str) -> str:
    if industry == "반도체" and phase in ("성장", "과열"):
        return "메모리 수출과 HBM은 강하지만 범용 DRAM 마진 정상화 시 피크아웃 우려가 빠르게 재부각될 수 있음"
    if phase == "초기 회복":
        return "초기 회복기에는 실적 확인 전 주가가 먼저 움직일 수 있어 공시와 주문 지표 확인이 필요"
    if phase == "과열":
        return "좋은 KPI가 이미 가격에 반영되었는지, 후행 수혜주까지 과도하게 확산되었는지 확인 필요"
    return "핵심 KPI가 실제 매출, 마진, 수주로 연결되는 시차를 확인해야 함"
