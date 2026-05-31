def _missing(value):
    if value is None:
        return "데이터 없음"
    if isinstance(value, (list, tuple)) and not value:
        return "데이터 없음"
    if hasattr(value, "empty") and value.empty:
        return "데이터 없음"
    return value


def generate_investment_note(
    stock_info: dict,
    financial_summary=None,
    valuation_summary=None,
    recent_news=None,
    recent_filings=None,
    event_summary=None,
    risk_flags=None,
) -> dict:
    name = stock_info.get("name", "종목명 없음")
    return {
        "왜 싸 보이는가": _missing(valuation_summary)
        if valuation_summary
        else f"{name}의 밸류에이션 점수와 섹터 대비 PER/PBR/PSR 위치를 확인해야 합니다.",
        "왜 지금 봐야 하는가": _missing(event_summary)
        if event_summary
        else "최근 이벤트 또는 실적 개선 신호가 있는지 추가 확인이 필요합니다.",
        "시장이 놓치고 있을 수 있는 포인트": "뉴스 기대감이 실제 수주, CAPEX, 협업, 원가 개선으로 연결되는지 검증할 여지가 있습니다.",
        "상승 촉매": "공식 공시, 후속 보도, 실적 가이던스 상향, 거래대금 지속성",
        "핵심 리스크": _missing(risk_flags),
        "추가 확인 지표": "분기 매출/영업이익 성장률, OCF/FCF, 부채비율, 재고/매출채권, 공시 원문",
        "관찰 결론": "매수 추천이 아니라 리서치 후보/관찰 후보입니다. 데이터와 출처를 확인한 뒤 투자 가설을 업데이트하세요.",
        "최근 뉴스": _missing(recent_news),
        "최근 공시": _missing(recent_filings),
        "재무 요약": _missing(financial_summary),
    }
