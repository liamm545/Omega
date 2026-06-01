from sector_intelligence.sector_registry import SECTOR_REGISTRY


SECOND_ORDER_MAP = {
    "AI / 데이터센터": ["전력기기", "클라우드 / 소프트웨어", "반도체", "자동차 / 로봇"],
    "반도체": ["반도체 장비", "반도체 소재", "패키징", "테스트", "전력기기"],
    "조선": ["조선 기자재", "엔진", "후판", "환율 수혜"],
    "방산": ["우주/위성", "레이더", "탄약", "항공 부품"],
    "전력기기": ["구리", "전선", "HVDC", "데이터센터 인프라"],
    "2차전지": ["ESS", "소재", "장비", "리사이클링"],
    "원전 / 에너지": ["터빈", "전력 인프라", "SMR", "건설/엔지니어링"],
    "자동차 / 로봇": ["전장", "센서", "감속기", "스마트팩토리"],
    "클라우드 / 소프트웨어": ["보안", "SI", "데이터 플랫폼", "AI SaaS"],
    "금융 / 지주 / 저PBR": ["배당", "자사주 소각", "밸류업 정책"],
}


def build_second_order_thesis(event: dict, stocks=None) -> dict:
    sectors = event.get("related_sectors") or []
    first_order = event.get("direct_beneficiaries") or []
    second = []
    for sector in sectors:
        second.extend(SECOND_ORDER_MAP.get(sector, []))
    second = sorted(set(second))
    candidate_stocks = _candidate_stocks(stocks, second)
    return {
        "event": event.get("event_name", "missing"),
        "first_order": first_order,
        "second_order": second,
        "third_order": ["실제 투자 규모", "수주 공시", "CAPEX 연결", "매출 기여", "거래대금 지속성"],
        "why_it_matters": "직접 수혜주가 급등한 뒤에는 실적 연결 고리가 있는 공급망과 인프라 쪽에서 덜 반영된 후보가 나올 수 있습니다.",
        "what_market_may_be_missing": "시장은 headline 직접 수혜주를 먼저 가격에 반영하고, 후행 수주/설비투자/인프라 증설 수혜는 늦게 반영할 수 있습니다.",
        "candidate_sectors": second,
        "candidate_stocks": candidate_stocks,
    }


def _candidate_stocks(stocks, groups: list[str]) -> list[dict]:
    if stocks is None or getattr(stocks, "empty", True):
        return []
    rows = []
    haystacks = [item.lower() for item in groups]
    for _, row in stocks.iterrows():
        text = f"{row.get('sector', '')} {row.get('industry', '')} {row.get('name', '')}".lower()
        if any(item.lower() in text for item in haystacks):
            rows.append({"ticker": row.get("ticker"), "name": row.get("name"), "reason": "2차 연결 산업 키워드 매칭"})
    return rows[:20]
