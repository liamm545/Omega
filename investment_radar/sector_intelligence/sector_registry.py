SECTOR_REGISTRY = {
    "반도체": {
        "stock_sectors": ["반도체"],
        "subsectors": ["메모리", "HBM", "파운드리", "반도체 장비", "반도체 소재", "패키징", "테스트", "팹리스"],
        "keywords": ["반도체", "메모리", "HBM", "D램", "DRAM", "낸드", "NAND", "파운드리", "장비", "소재", "패키징", "테스트"],
        "beneficiary_groups": ["메모리 대형주", "HBM 공급망", "장비", "소재", "패키징/테스트"],
        "risks": ["피크아웃 논란", "범용 메모리 가격 정상화", "CAPEX 과잉", "AI 서버 수요 둔화"],
        "watch_points": ["D램/NAND 가격", "HBM 성장률", "CAPEX 증가 여부", "장비주 수주 연결"],
    },
    "AI / 데이터센터": {
        "stock_sectors": ["인터넷", "IT서비스", "전자", "반도체", "전력기기"],
        "subsectors": ["GPU", "데이터센터 인프라", "전력설비", "냉각", "광통신", "서버", "클라우드", "AI 소프트웨어"],
        "keywords": ["AI", "GPU", "데이터센터", "클라우드", "서버", "전력", "냉각", "광통신", "엔비디아", "NVIDIA"],
        "beneficiary_groups": ["클라우드", "데이터센터 인프라", "전력설비", "서버/광통신", "AI 소프트웨어"],
        "risks": ["GPU 공급 병목", "전력 비용 상승", "CAPEX 회수 지연", "기대감 선반영"],
        "watch_points": ["실제 계약", "GPU 공급", "데이터센터 증설", "전력 사용량 증가"],
    },
    "클라우드 / 소프트웨어": {
        "stock_sectors": ["인터넷", "IT서비스", "소프트웨어"],
        "subsectors": ["NAVER Cloud", "AI SaaS", "보안", "ERP", "SI", "데이터 플랫폼"],
        "keywords": ["클라우드", "SaaS", "보안", "ERP", "SI", "데이터 플랫폼", "AI 소프트웨어"],
        "beneficiary_groups": ["클라우드 플랫폼", "SI", "보안", "AI SaaS"],
        "risks": ["마진 둔화", "경쟁 심화", "레퍼런스의 매출 전환 지연"],
        "watch_points": ["계약 규모", "ARR/매출 전환", "GPU/IDC 투자"],
    },
    "조선": {
        "stock_sectors": ["조선"],
        "subsectors": ["조선사", "조선 기자재", "LNG선", "해양플랜트", "엔진", "후판", "환율 수혜"],
        "keywords": ["조선", "LNG선", "수주", "신조선가", "후판", "엔진", "해양플랜트"],
        "beneficiary_groups": ["조선사", "엔진", "기자재", "LNG선 공급망"],
        "risks": ["후판 가격 상승", "원화 강세", "인도 지연", "수주 공백"],
        "watch_points": ["신조선가지수", "수주잔고", "후판 가격", "환율"],
    },
    "방산": {
        "stock_sectors": ["방산"],
        "subsectors": ["항공", "유도무기", "장갑차", "탄약", "레이더", "우주/위성", "수출 계약"],
        "keywords": ["방산", "수출 계약", "항공", "유도무기", "장갑차", "탄약", "레이더", "위성", "국방비"],
        "beneficiary_groups": ["항공/엔진", "유도무기", "지상무기", "우주/위성"],
        "risks": ["계약 지연", "정책 변화", "지정학 리스크 완화", "환율 변동"],
        "watch_points": ["수출 계약", "정부 정책", "NATO/중동 수요", "수주잔고"],
    },
    "전력기기": {
        "stock_sectors": ["전력기기", "전기장비"],
        "subsectors": ["변압기", "전선", "전력망", "HVDC", "구리 가격", "미국 전력 인프라 투자"],
        "keywords": ["변압기", "전선", "전력망", "HVDC", "구리", "전력 인프라", "그리드"],
        "beneficiary_groups": ["변압기", "전선", "HVDC", "전력망 장비"],
        "risks": ["구리 가격 급등", "미국 투자 지연", "마진 피크아웃"],
        "watch_points": ["구리 가격", "전력망 투자", "변압기 수출", "수주잔고"],
    },
    "2차전지": {
        "stock_sectors": ["2차전지", "배터리"],
        "subsectors": ["셀", "양극재", "음극재", "전해액", "분리막", "리튬", "ESS"],
        "keywords": ["2차전지", "배터리", "양극재", "음극재", "전해액", "분리막", "리튬", "ESS", "전기차"],
        "beneficiary_groups": ["셀", "소재", "장비", "ESS"],
        "risks": ["전기차 수요 둔화", "재고 조정", "리튬 가격 하락", "마진 압박"],
        "watch_points": ["리튬/니켈 가격", "EV 판매", "ESS 수요", "고객사 재고"],
    },
    "원전 / 에너지": {
        "stock_sectors": ["원전", "에너지"],
        "subsectors": ["원전 수출", "SMR", "터빈", "전력 인프라", "LNG", "재생에너지"],
        "keywords": ["원전", "SMR", "터빈", "LNG", "재생에너지", "전력 인프라"],
        "beneficiary_groups": ["원전 주기기", "터빈", "전력 인프라", "SMR"],
        "risks": ["정책 지연", "수출 금융", "프로젝트 지연"],
        "watch_points": ["원전 수출", "정책 발표", "수주 공시", "전력 수요"],
    },
    "자동차 / 로봇": {
        "stock_sectors": ["자동차", "로봇", "전자"],
        "subsectors": ["전장", "자율주행", "로봇 부품", "감속기", "센서", "스마트팩토리"],
        "keywords": ["전장", "자율주행", "로봇", "감속기", "센서", "스마트팩토리"],
        "beneficiary_groups": ["전장", "로봇 부품", "센서", "스마트팩토리"],
        "risks": ["양산 지연", "고객사 투자 지연", "테마 과열"],
        "watch_points": ["수주", "양산 일정", "고객사 CAPEX", "마진"],
    },
    "금융 / 지주 / 저PBR": {
        "stock_sectors": ["금융", "지주", "은행", "보험", "증권"],
        "subsectors": ["밸류업", "배당", "자사주 소각", "금리", "ROE", "주주환원"],
        "keywords": ["밸류업", "배당", "자사주", "소각", "금리", "ROE", "주주환원", "저PBR"],
        "beneficiary_groups": ["은행", "보험", "증권", "지주"],
        "risks": ["금리 하락", "규제", "대손비용", "주주환원 기대 선반영"],
        "watch_points": ["PBR", "ROE", "배당수익률", "자사주 소각"],
    },
}


def sector_for_stock_sector(stock_sector: str) -> str:
    for sector, config in SECTOR_REGISTRY.items():
        if stock_sector in config.get("stock_sectors", []):
            return sector
    return stock_sector or "missing"


def all_sector_names() -> list[str]:
    return list(SECTOR_REGISTRY.keys())
