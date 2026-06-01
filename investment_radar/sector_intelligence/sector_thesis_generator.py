from __future__ import annotations

import json

import pandas as pd

from utils.env import get_env


def generate_sector_thesis(sector_row: dict, context: dict | None = None) -> dict:
    if get_env("OPENAI_API_KEY"):
        generated = _try_llm(sector_row, context or {})
        if generated:
            return generated
    return {
        "현재 산업 국면": sector_row.get("cycle_stage", "UNKNOWN"),
        "핵심 근거": _list_text(sector_row.get("positive_signals_json")),
        "반대 시나리오": _list_text(sector_row.get("negative_signals_json")),
        "체크포인트": _list_text(sector_row.get("watch_points_json")),
        "수혜 업종": _list_text(sector_row.get("beneficiary_groups_json")),
        "투자자가 놓치기 쉬운 부분": "직접 수혜주 급등 이후에도 후행 수주, CAPEX, 인프라 증설이 2차 수혜로 연결되는지 확인해야 합니다.",
    }


def _try_llm(sector_row: dict, context: dict) -> dict:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=get_env("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=get_env("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "입력된 수치와 근거만 사용해 섹터 투자 가설을 JSON으로 작성한다. 없는 수치는 만들지 말고 missing으로 표시한다. 매수/매도 표현 금지."},
                {"role": "user", "content": json.dumps({"sector": sector_row, "context": context}, ensure_ascii=False)},
            ],
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {}


def _list_text(value) -> str:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return value or "missing"
    if isinstance(value, list):
        return ", ".join([str(item) for item in value]) or "missing"
    return "missing"
