from datetime import datetime
import re

import pandas as pd

from data_collectors.naver_news_collector import NaverNewsCollector
from industry_intelligence.industry_registry import INDUSTRY_REGISTRY
from utils.text_cleaner import clean_text


PERCENT_PATTERN = re.compile(r"([-+]?\d+(?:\.\d+)?)\s*%")
NUMBER_PATTERN = re.compile(r"([-+]?\d+(?:\.\d+)?)")


def collect_industry_kpis_from_news(display: int = 5) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    collector = NaverNewsCollector()
    failures = []
    if not collector.client_id or not collector.client_secret:
        return _empty_kpis(), _empty_evidence(), ["NAVER_CLIENT_ID/NAVER_CLIENT_SECRET missing"]

    evidence_rows = []
    kpi_rows = []
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for industry, config in INDUSTRY_REGISTRY.items():
        for kpi, spec in config.get("kpi_news_queries", {}).items():
            candidates = []
            for query in spec.get("queries", []):
                news = collector.search_news(query=query, display=display, sort="date")
                if news.empty:
                    failures.append(f"{industry}/{kpi}/{query}: {collector.last_error or 'no result'}")
                    continue
                for _, item in news.iterrows():
                    text = f"{item.get('title', '')} {item.get('description', '')}"
                    extracted = extract_kpi_value(text, aliases=spec.get("aliases", []), unit=spec.get("unit"))
                    if extracted is None:
                        continue
                    row = {
                        "collected_at": collected_at,
                        "published_at": _to_date(item.get("pubDate")),
                        "industry": industry,
                        "kpi": kpi,
                        "query": query,
                        "value": extracted,
                        "unit": spec.get("unit", ""),
                        "title": clean_text(item.get("title", "")),
                        "url": item.get("link", ""),
                        "summary": clean_text(item.get("description", "")),
                        "source": "NAVER_NEWS_EXTRACTED",
                    }
                    evidence_rows.append(row)
                    candidates.append(row)

            if candidates:
                best = _select_best_candidate(candidates)
                kpi_rows.append(
                    {
                        "date": best["published_at"] or collected_at[:10],
                        "industry": industry,
                        "kpi": kpi,
                        "value": best["value"],
                        "unit": best["unit"],
                        "change_1m": None,
                        "change_3m": None,
                        "source": "NAVER_NEWS_EXTRACTED",
                        "evidence_url": best["url"],
                    }
                )

    return (
        pd.DataFrame(kpi_rows, columns=_kpi_columns()),
        pd.DataFrame(evidence_rows, columns=_evidence_columns()),
        failures,
    )


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
