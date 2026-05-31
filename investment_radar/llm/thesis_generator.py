from typing import Optional

def generate_thesis(stock_row: dict, event_row: Optional[dict] = None) -> dict:
    event_reason = event_row.get("reason", "관련 이벤트 없음") if event_row else "관련 이벤트 없음"
    return {
        "저평가 근거": "섹터 대비 밸류에이션 점수와 현금흐름 점수를 함께 확인하세요.",
        "이벤트 근거": event_reason,
        "상승 촉매": "공식 공시, 수주, CAPEX, 실적 개선 확인 시 가설 강화",
        "핵심 리스크": "단기 기대감 선반영, 실적 미연결, 뉴스 출처 불명확성",
        "추가 확인 지표": "분기 실적, 거래대금 지속성, 공시 원문, 컨퍼런스콜 코멘트",
    }
