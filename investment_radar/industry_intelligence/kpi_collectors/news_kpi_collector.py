from datetime import datetime
import json
import re

import pandas as pd

from data_collectors.naver_news_collector import NaverNewsCollector
from industry_intelligence.industry_registry import INDUSTRY_REGISTRY
from utils.env import get_env
from utils.text_cleaner import clean_text


PERCENT_PATTERN = re.compile(r"([-+]?\d+(?:\.\d+)?)\s*%")
NUMBER_PATTERN = re.compile(r"([-+]?\d+(?:\.\d+)?)")


def collect_industry_kpis_from_news(display: int = 5) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    collector = NaverNewsCollector()
    failures = []
    if not collector.client_id or not collector.client_secret:
        return _empty_kpis(), _empty_evidence(), ["NAVER_CLIENT_ID/NAVER_CLIENT_SECRET missing"]

    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    candidates = []
    candidate_id = 1

    for industry, config in INDUSTRY_REGISTRY.items():
        for kpi, spec in config.get("kpi_news_queries", {}).items():
            for query in spec.get("queries", []):
                news = collector.search_news(query=query, display=display, sort="date")
                if news.empty:
                    failures.append(f"{industry}/{kpi}/{query}: {collector.last_error or 'no result'}")
                    continue
                for _, item in news.iterrows():
                    candidates.append(
                        {
                            "candidate_id": candidate_id,
                            "industry": industry,
                            "kpi": kpi,
                            "unit": spec.get("unit", ""),
                            "aliases": spec.get("aliases", []),
                            "query": query,
                            "published_at": _to_date(item.get("pubDate")),
                            "title": clean_text(item.get("title", ""))[:220],
                            "url": item.get("link", ""),
                            "summary": clean_text(item.get("description", ""))[:360],
                        }
                    )
                    candidate_id += 1

    if not candidates:
        return _empty_kpis(), _empty_evidence(), failures

    extracted_items = _extract_with_llm(candidates)
    if not extracted_items:
        extracted_items = _extract_with_regex(candidates)

    evidence_rows = []
    kpi_rows = []
    candidate_map = {item["candidate_id"]: item for item in candidates}
    grouped = {}
    for item in extracted_items:
        source = candidate_map.get(item.get("candidate_id"))
        if not source or item.get("value") is None:
            continue
        evidence = {
                        "collected_at": collected_at,
            "published_at": source.get("published_at", ""),
            "industry": source["industry"],
            "kpi": source["kpi"],
            "query": source["query"],
            "value": float(item["value"]),
            "unit": item.get("unit") or source.get("unit", ""),
            "title": source["title"],
            "url": source["url"],
            "summary": _evidence_summary(source, item),
            "source": item.get("source", "NAVER_NEWS_LLM_EXTRACTED"),
        }
        evidence_rows.append(evidence)
        key = (evidence["industry"], evidence["kpi"])
        grouped.setdefault(key, []).append(evidence)

    for _, rows in grouped.items():
        best = _select_best_candidate(rows)
        kpi_rows.append(
            {
                "date": best["published_at"] or collected_at[:10],
                "industry": best["industry"],
                "kpi": best["kpi"],
                "value": best["value"],
                "unit": best["unit"],
                "change_1m": None,
                "change_3m": None,
                "source": best["source"],
                "evidence_url": best["url"],
            }
        )

    return (
        pd.DataFrame(kpi_rows, columns=_kpi_columns()),
        pd.DataFrame(evidence_rows, columns=_evidence_columns()),
        failures,
    )


def _extract_with_llm(candidates: list[dict]) -> list[dict]:
    api_key = get_env("OPENAI_API_KEY")
    if not api_key:
        return []
    try:
        from openai import OpenAI

        compact = [
            {
                "candidate_id": item["candidate_id"],
                "industry": item["industry"],
                "kpi": item["kpi"],
                "expected_unit": item["unit"],
                "title": item["title"],
                "summary": item["summary"],
                "url": item["url"],
            }
            for item in candidates[:80]
        ]
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=get_env("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            messages=[
                {"role": "system", "content": _kpi_extraction_prompt()},
                {"role": "user", "content": json.dumps({"candidates": compact}, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
        )
        payload = json.loads(response.choices[0].message.content)
        return [
            {
                "candidate_id": int(item["candidate_id"]),
                "value": float(item["value"]),
                "unit": item.get("unit", ""),
                "confidence": float(item.get("confidence", 0)),
                "reason": item.get("reason", ""),
                "source": "NAVER_NEWS_LLM_EXTRACTED",
            }
            for item in payload.get("items", [])
            if item.get("candidate_id") is not None and item.get("value") is not None and float(item.get("confidence", 0)) >= 0.55
        ]
    except Exception:
        return []


def _extract_with_regex(candidates: list[dict]) -> list[dict]:
    extracted = []
    for item in candidates:
        value = extract_kpi_value(f"{item['title']} {item['summary']}", aliases=item.get("aliases", []), unit=item.get("unit"))
        if value is None:
            continue
        extracted.append(
            {
                "candidate_id": item["candidate_id"],
                "value": value,
                "unit": item.get("unit", ""),
                "confidence": 0.35,
                "reason": "regex fallback",
                "source": "NAVER_NEWS_REGEX_EXTRACTED",
            }
        )
    return extracted


def _kpi_extraction_prompt() -> str:
    return (
        "너는 산업 KPI 추출기다. 입력 기사 후보의 title/summary에 명시된 수치만 추출한다. "
        "추론하거나 외부 지식으로 수치를 만들지 마라. candidate_id별로 해당 KPI의 실제 수치라고 판단되는 경우만 반환한다. "
        "단순 날짜, 기업명 숫자, 주가, 목표가, 순위, 분기 번호는 KPI 값으로 쓰지 마라. "
        "반드시 JSON object로 답한다: {\"items\":[{\"candidate_id\":정수,\"value\":숫자,\"unit\":\"단위\",\"confidence\":0~1,\"reason\":\"짧은 근거\"}]}. "
        "애매하면 items에 넣지 마라."
    )


def _evidence_summary(source: dict, item: dict) -> str:
    reason = item.get("reason") or ""
    confidence = item.get("confidence")
    suffix = f" | extraction_confidence={confidence}" if confidence is not None else ""
    return f"{source.get('summary', '')} | extraction_reason={reason}{suffix}"


def extract_kpi_value(text: str, aliases: list[str] = None, unit: str = ""):
    cleaned = clean_text(text)
    aliases = aliases or []
    if "%" in unit or "%" in cleaned:
        value = _extract_near_alias(cleaned, aliases, PERCENT_PATTERN)
        if value is not None:
            return value
        matches = PERCENT_PATTERN.findall(cleaned)
        return float(matches[0]) if matches else None
    value = _extract_near_alias(cleaned, aliases, NUMBER_PATTERN)
    if value is not None:
        return value
    matches = NUMBER_PATTERN.findall(cleaned)
    return float(matches[0]) if matches else None


def _extract_near_alias(text: str, aliases: list[str], pattern: re.Pattern):
    lower_text = text.lower()
    best = None
    best_distance = None
    for match in pattern.finditer(text):
        value_position = match.start()
        for alias in aliases:
            alias_position = lower_text.find(alias.lower())
            if alias_position == -1:
                continue
            distance = abs(value_position - alias_position)
            if best_distance is None or distance < best_distance:
                best = float(match.group(1))
                best_distance = distance
    return best


def _select_best_candidate(candidates: list[dict]) -> dict:
    dated = [candidate for candidate in candidates if candidate.get("published_at")]
    if dated:
        return sorted(dated, key=lambda item: item["published_at"], reverse=True)[0]
    return candidates[0]


def _to_date(value) -> str:
    if not value:
        return ""
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%Y-%m-%d")


def _kpi_columns() -> list[str]:
    return ["date", "industry", "kpi", "value", "unit", "change_1m", "change_3m", "source", "evidence_url"]


def _evidence_columns() -> list[str]:
    return ["collected_at", "published_at", "industry", "kpi", "query", "value", "unit", "title", "url", "summary", "source"]


def _empty_kpis() -> pd.DataFrame:
    return pd.DataFrame(columns=_kpi_columns())


def _empty_evidence() -> pd.DataFrame:
    return pd.DataFrame(columns=_evidence_columns())
