from datetime import date

import pandas as pd

from industry_intelligence.industry_registry import INDUSTRY_REGISTRY


CYCLE_PHASES = ["침체", "초기 회복", "성장", "과열", "정점"]


def detect_industry_cycles(industry_kpis: pd.DataFrame, as_of: str = None) -> pd.DataFrame:
    if industry_kpis.empty:
        return pd.DataFrame(columns=_signal_columns())

    as_of = as_of or industry_kpis["date"].max() or date.today().isoformat()
    rows = []
    for industry, kpis in industry_kpis.groupby("industry"):
        latest = kpis.sort_values("date").groupby("kpi", as_index=False).tail(1)
        score = _cycle_score(latest)
        phase = _phase_from_score(score, latest)
        positive = _format_evidence(latest[latest["value"].fillna(0) > 0], limit=5)
        negative = _format_evidence(latest[latest["value"].fillna(0) < 0], limit=3)
        config = INDUSTRY_REGISTRY.get(industry, {})
        checkpoints = _checkpoints(industry, latest)
        rows.append(
            {
                "date": as_of,
                "industry": industry,
                "cycle_phase": phase,
                "cycle_score": round(score, 1),
                "confidence": _confidence(latest, config),
                "key_kpis": ", ".join(latest["kpi"].tolist()[:8]),
                "positive_evidence": positive or "missing",
                "negative_evidence": negative or "missing",
                "checkpoints": " | ".join(checkpoints),
                "beneficiaries": ", ".join(config.get("beneficiaries", [])) or "missing",
                "risks": ", ".join(config.get("risks", [])) or "missing",
            }
        )
    return pd.DataFrame(rows, columns=_signal_columns())


def _cycle_score(kpis: pd.DataFrame) -> float:
    if kpis.empty:
        return 0.0
    value_score = kpis["value"].fillna(0).clip(-100, 300).mean() / 3
    change_1m = kpis["change_1m"].fillna(0).clip(-50, 100).mean() * 0.35
    change_3m = kpis["change_3m"].fillna(0).clip(-100, 200).mean() * 0.20
    breadth = (kpis["value"].fillna(0) > 0).mean() * 20
    return max(0.0, min(100.0, value_score + change_1m + change_3m + breadth))


def _phase_from_score(score: float, kpis: pd.DataFrame) -> str:
    strong_growth = (kpis["value"].fillna(0) >= 100).sum()
    if score >= 82 and strong_growth >= 2:
        return "과열"
    if score >= 68:
        return "성장"
    if score >= 48:
        return "초기 회복"
    if score >= 32:
        return "정점"
    return "침체"


def _confidence(kpis: pd.DataFrame, config: dict) -> float:
    expected = len(config.get("core_kpis", [])) or len(kpis)
    coverage = min(1.0, len(kpis) / max(expected, 1))
    sourced = (kpis["source"].fillna("").ne("")).mean() if not kpis.empty else 0
    return round((coverage * 70) + (sourced * 30), 1)


def _format_evidence(kpis: pd.DataFrame, limit: int) -> str:
    parts = []
    for _, row in kpis.sort_values("value", ascending=False).head(limit).iterrows():
        value = row.get("value")
        unit = row.get("unit") or ""
        parts.append(f"{row.get('kpi')}: {value:g}{unit}")
    return " | ".join(parts)


def _checkpoints(industry: str, kpis: pd.DataFrame) -> list[str]:
    if industry == "반도체":
        return ["HBM 성장률 둔화 여부", "DRAM/NAND 가격 상승 지속 여부", "삼성전자/SK하이닉스 CAPEX 변화"]
    if industry == "조선":
        return ["신조선가지수 유지 여부", "후판가격 상승 여부", "수주잔고의 매출 전환 속도"]
    if industry == "전력기기":
        return ["구리 가격 전가 가능성", "미국 전력망 투자 지연 여부", "수주잔고 마진율"]
    if industry == "방산":
        return ["수출 계약의 본계약 전환", "인도 일정", "환율과 원가 변동"]
    if industry == "AI 인프라":
        return ["데이터센터 CAPEX 지속 여부", "GPU 공급 병목 완화", "전력/냉각 비용"]
    return ["핵심 KPI 추세 유지 여부", "뉴스가 공시/실적으로 연결되는지", "가격에 선반영된 정도"]


def _signal_columns() -> list[str]:
    return [
        "date",
        "industry",
        "cycle_phase",
        "cycle_score",
        "confidence",
        "key_kpis",
        "positive_evidence",
        "negative_evidence",
        "checkpoints",
        "beneficiaries",
        "risks",
    ]
