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
    if event.get("relation_grade") == "NEGATIVE" or event.get("sentiment") == "NEGATIVE":
        return {
            "event": event.get("event_name", "missing"),
            "first_order": [],
            "second_order": [],
            "third_order": ["사고/규제의 실제 비용", "수주잔고 훼손 여부", "보험/충당금", "정부 제재 가능성", "주가 하락 과잉 여부"],
            "why_it_matters": "악재성 이벤트는 수혜주 탐색보다 실적 훼손 범위와 주가 과잉 반응 여부를 먼저 검증해야 합니다.",
            "what_market_may_be_missing": "단기 공포로 주가가 급락했더라도 장기 수주잔고, 경쟁력, 정책 수요가 유지되는지 분리해서 봐야 합니다.",
            "candidate_sectors": [],
            "candidate_stocks": [],
        }
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
        "why_it_matters": _why_it_matters(event, second),
        "what_market_may_be_missing": _market_may_miss(event, second),
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


def _why_it_matters(event: dict, second: list[str]) -> str:
    event_type = event.get("event_type")
    if event_type in {"CAPEX", "POLICY"}:
        return "투자/정책 이벤트는 직접 기업보다 설비, 전력, 장비, 소재처럼 지출이 흘러가는 후방 공급망에서 실적 연결이 늦게 나타날 수 있습니다."
    if event_type in {"SUPPLY_CONTRACT", "EXPORT_DATA", "INDUSTRY_DATA"}:
        return "수주·수출·산업 데이터는 대형주 실적 기대를 먼저 움직이고, 이후 장비/소재/부품의 주문 증가 여부가 후행 확인 포인트가 됩니다."
    if event_type in {"CEO_MEETING", "KEYNOTE_MENTION", "MOU"}:
        return "언급·회동·MOU는 기대감이 먼저 반영되기 쉽기 때문에 실제 계약, GPU/IDC 투자, 매출 전환으로 이어질 공급망을 분리해야 합니다."
    return "이벤트가 실적에 연결되는 경로를 직접 기업, 공급망, 인프라, 후행 투자 순서로 분해해 봐야 합니다."


def _market_may_miss(event: dict, second: list[str]) -> str:
    if not second:
        return "현재 뉴스만으로는 명확한 2차 수혜 연결고리가 약합니다. 공식 공시와 후속 데이터를 기다리는 편이 낫습니다."
    return f"시장은 직접 언급 기업을 먼저 가격에 반영할 수 있습니다. 아직 확인할 부분은 {', '.join(second[:3])}의 실제 수주/매출 연결 여부입니다."
