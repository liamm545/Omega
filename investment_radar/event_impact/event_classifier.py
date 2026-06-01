EVENT_TYPE_RULES = {
    "NEGATIVE_INCIDENT": ["참사", "사고", "폭발", "화재", "사망", "부상", "책임", "조사", "압수수색", "기소", "소송", "제재", "리콜", "관리 책임"],
    "NEGATIVE_REGULATION": ["규제", "제재", "수출통제", "벌금", "과징금", "영업정지"],
    "CEO_MEETING": ["회동", "면담", "방한", "방문", "meeting"],
    "KEYNOTE_MENTION": ["기조연설", "언급", "파트너로 소개", "keynote"],
    "SUPPLY_CONTRACT": ["공급 계약", "수주", "계약 체결", "납품", "공급"],
    "CAPEX": ["CAPEX", "투자", "증설", "설비투자", "데이터센터 투자"],
    "MOU": ["MOU", "업무협약", "협력"],
    "POLICY": ["정책", "정부", "지원책", "규제 완화"],
    "EXPORT_DATA": ["수출", "증가율", "무역", "통계"],
    "EARNINGS_SURPRISE": ["어닝", "실적", "영업이익", "컨센서스 상회"],
    "GUIDANCE_CHANGE": ["가이던스", "전망 상향", "목표"],
    "GEOPOLITICAL": ["지정학", "전쟁", "중동", "NATO", "방위비"],
    "COMMODITY_SHOCK": ["구리", "리튬", "니켈", "WTI", "천연가스", "원자재"],
    "REGULATION": ["규제 완화", "허가", "승인"],
    "INDEX_REBALANCING": ["MSCI", "편입", "리밸런싱", "비중 확대"],
    "INDUSTRY_DATA": ["신조선가", "수주잔고", "DRAM 가격", "D램 가격", "HBM 성장률"],
    "TECHNOLOGY_BREAKTHROUGH": ["신기술", "양산", "돌파구", "세계 최초"],
}


def classify_event_type(text: str) -> str:
    normalized = (text or "").lower()
    for event_type, keywords in EVENT_TYPE_RULES.items():
        if any(keyword.lower() in normalized for keyword in keywords):
            return event_type
    return "INDUSTRY_DATA"


def relation_grade(event_type: str, has_ticker: bool = True) -> str:
    if event_type.startswith("NEGATIVE"):
        return "NEGATIVE"
    if event_type in {"SUPPLY_CONTRACT", "CAPEX", "EARNINGS_SURPRISE", "GUIDANCE_CHANGE"} and has_ticker:
        return "DIRECT"
    if event_type in {"CEO_MEETING", "KEYNOTE_MENTION", "MOU"}:
        return "DIRECT" if has_ticker else "SECTOR_THEME"
    if event_type in {"COMMODITY_SHOCK", "POLICY", "EXPORT_DATA", "INDUSTRY_DATA", "GEOPOLITICAL"}:
        return "SECTOR_THEME"
    return "SPECULATIVE"
