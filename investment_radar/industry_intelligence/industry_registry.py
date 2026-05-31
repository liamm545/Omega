INDUSTRY_REGISTRY = {
    "반도체": {
        "stock_sectors": ["반도체"],
        "beneficiary_keywords": ["HBM", "DRAM", "NAND", "메모리", "장비", "소재"],
        "core_kpis": [
            "메모리 수출 증가율",
            "D램 수출 증가율",
            "낸드 수출 증가율",
            "HBM 성장률",
            "DRAM 가격",
            "필라델피아 반도체지수",
            "삼성전자 CAPEX",
            "SK하이닉스 CAPEX",
        ],
        "beneficiaries": ["삼성전자", "SK하이닉스", "한미반도체", "HPSP"],
        "risks": ["범용 메모리 가격 정상화", "CAPEX 과잉", "AI 서버 수요 둔화"],
        "kpi_news_queries": {
            "메모리 수출 증가율": {
                "queries": ["한국 메모리 반도체 수출 증가율", "메모리 수출 증가율 HBM DRAM NAND"],
                "aliases": ["메모리", "memory"],
                "unit": "% YoY",
            },
            "D램 수출 증가율": {
                "queries": ["D램 수출 증가율", "DRAM exports Korea growth"],
                "aliases": ["D램", "DRAM"],
                "unit": "% YoY",
            },
            "낸드 수출 증가율": {
                "queries": ["낸드 수출 증가율", "NAND exports Korea growth"],
                "aliases": ["낸드", "NAND"],
                "unit": "% YoY",
            },
            "HBM 성장률": {
                "queries": ["HBM 성장률 수출 증가율", "HBM exports Korea growth"],
                "aliases": ["HBM", "고대역폭메모리"],
                "unit": "% YoY",
            },
            "DRAM 가격": {
                "queries": ["DRAM 가격 상승률", "D램 가격 상승률"],
                "aliases": ["DRAM", "D램"],
                "unit": "%",
            },
        },
    },
    "조선": {
        "stock_sectors": ["조선"],
        "core_kpis": ["신조선가지수", "수주잔고", "후판가격", "환율"],
        "beneficiaries": ["삼성중공업", "HD현대중공업", "한화오션"],
        "risks": ["후판가격 상승", "원화 강세", "인도 지연"],
        "kpi_news_queries": {
            "신조선가지수": {
                "queries": ["신조선가지수 상승", "Clarksons newbuilding price index Korea"],
                "aliases": ["신조선가지수", "newbuilding"],
                "unit": "pt",
            },
            "수주잔고": {
                "queries": ["조선 수주잔고 증가", "한국 조선 수주잔고"],
                "aliases": ["수주잔고", "orderbook"],
                "unit": "%",
            },
        },
    },
    "전력기기": {
        "stock_sectors": ["전력기기", "전기장비"],
        "core_kpis": ["미국 변압기 가격", "구리 가격", "전력설비 투자액"],
        "beneficiaries": ["HD현대일렉트릭", "효성중공업", "LS ELECTRIC"],
        "risks": ["구리 가격 급등", "미국 전력망 투자 지연"],
        "kpi_news_queries": {
            "미국 변압기 가격": {
                "queries": ["미국 변압기 가격 상승 전력기기", "US transformer price increase"],
                "aliases": ["변압기", "transformer"],
                "unit": "%",
            },
            "전력설비 투자액": {
                "queries": ["미국 전력설비 투자 증가", "power grid investment growth"],
                "aliases": ["전력설비", "grid investment"],
                "unit": "%",
            },
        },
    },
    "방산": {
        "stock_sectors": ["방산"],
        "core_kpis": ["글로벌 국방예산", "수출 계약"],
        "beneficiaries": ["한화에어로스페이스", "LIG넥스원", "현대로템"],
        "risks": ["계약 지연", "정책 변화", "환율 변동"],
        "kpi_news_queries": {
            "수출 계약": {
                "queries": ["방산 수출 계약 규모", "한국 방산 수출 계약"],
                "aliases": ["수출 계약", "방산"],
                "unit": "억원",
            },
        },
    },
    "AI 인프라": {
        "stock_sectors": ["인터넷", "IT서비스", "반도체", "전자"],
        "core_kpis": ["데이터센터 투자", "GPU 공급량", "엔비디아 CAPEX"],
        "beneficiaries": ["NAVER", "LG전자", "LG CNS", "삼성전자", "SK하이닉스"],
        "risks": ["GPU 공급 병목", "전력 비용 상승", "CAPEX 회수 지연"],
        "kpi_news_queries": {
            "데이터센터 투자": {
                "queries": ["데이터센터 투자 증가율 AI 인프라", "AI data center investment growth"],
                "aliases": ["데이터센터", "data center"],
                "unit": "%",
            },
            "GPU 공급량": {
                "queries": ["GPU 공급량 증가 AI 서버", "GPU supply growth AI server"],
                "aliases": ["GPU"],
                "unit": "%",
            },
            "엔비디아 CAPEX": {
                "queries": ["엔비디아 CAPEX 증가 데이터센터", "NVIDIA capex data center growth"],
                "aliases": ["엔비디아", "NVIDIA", "CAPEX"],
                "unit": "%",
            },
        },
    },
}


def industry_for_sector(sector: str) -> str:
    for industry, config in INDUSTRY_REGISTRY.items():
        if sector in config.get("stock_sectors", []):
            return industry
    return sector or "missing"
