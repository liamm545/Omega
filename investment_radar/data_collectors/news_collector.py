from data_collectors.naver_news_collector import NaverNewsCollector


def collect_news(query: str, start_date: str = None, end_date: str = None):
    """Backward-compatible wrapper around NaverNewsCollector."""
    return NaverNewsCollector().search_news(query=query)
