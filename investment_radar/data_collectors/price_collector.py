from data_collectors.krx_collector import KrxCollector


def collect_prices(ticker: str, start_date: str, end_date: str):
    """Collect prices through KRX API, with pykrx/sample fallback."""
    return KrxCollector().get_daily_price(ticker=ticker, start_date=start_date, end_date=end_date)
