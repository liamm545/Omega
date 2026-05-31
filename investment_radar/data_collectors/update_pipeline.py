from datetime import date, timedelta

import pandas as pd

from data_collectors.dart_collector import DartCollector
from data_collectors.krx_collector import KrxCollector
from data_collectors.macro_collector import collect_macro_indicators_with_diagnostics
from data_collectors.naver_news_collector import NaverNewsCollector
from database.db import load_table, log_update, upsert_rows
from industry_intelligence.kpi_collectors.news_kpi_collector import collect_industry_kpis_from_news
from utils.env import get_env
from utils.logger import get_logger


logger = get_logger(__name__)


def update_stock_master(conn) -> dict:
    collector = KrxCollector()
    master = collector.get_stock_master()
    if master.empty:
        log_update(conn, "pykrx.stock_master", "failed", 0, "종목 마스터를 가져오지 못했습니다.")
        return {"stocks": 0}
    existing = load_table(conn, "stocks")
    if not existing.empty:
        base = master.merge(existing[["ticker", "sector", "industry"]], on="ticker", how="left", suffixes=("", "_existing"))
        base["sector"] = base["sector_existing"].fillna(base["sector"])
        base["industry"] = base["industry_existing"].fillna(base["industry"])
        master = base[["ticker", "name", "market", "sector", "industry", "market_cap"]]
    count = upsert_rows(conn, "stocks", master, ["ticker"])
    log_update(conn, "pykrx.stock_master", "success", count, "종목 마스터 업데이트 완료")
    return {"stocks": count}


def update_pykrx_prices(conn, tickers: list[str] = None, start_date: str = None, end_date: str = None) -> dict:
    collector = KrxCollector()
    if tickers is None:
        tickers = load_table(conn, "stocks")["ticker"].dropna().head(30).tolist()
    if end_date is None:
        end_date = date.today().strftime("%Y%m%d")
    if start_date is None:
        start_date = get_env("INVESTMENT_RADAR_DEFAULT_START_DATE") or (date.today() - timedelta(days=180)).strftime("%Y%m%d")

    total = 0
    failed = []
    for ticker in tickers:
        prices = collector.get_daily_price(ticker, start_date, end_date)
        if prices.empty:
            failed.append(ticker)
            continue
        conn.execute("DELETE FROM daily_prices WHERE ticker = ?", (ticker,))
        conn.commit()
        total += upsert_rows(conn, "daily_prices", prices, ["date", "ticker"])
    status = "partial" if failed and total else "failed" if failed else "success"
    message = f"기간 {start_date}~{end_date}, 실패 {len(failed)}건: {', '.join(failed[:10])}" if failed else f"기간 {start_date}~{end_date}"
    log_update(conn, "pykrx.daily_prices", status, total, message)
    return {"daily_prices": total, "price_failed": failed}


def update_market_caps(conn, date_yyyymmdd: str = None) -> dict:
    collector = KrxCollector()
    date_yyyymmdd = date_yyyymmdd or date.today().strftime("%Y%m%d")
    caps = collector.get_market_cap(date_yyyymmdd)
    if caps.empty:
        log_update(conn, "pykrx.market_cap", "failed", 0, f"{date_yyyymmdd} 시총 데이터를 가져오지 못했습니다.")
        return {"market_cap": 0}
    stocks = load_table(conn, "stocks")
    existing_caps = stocks[["ticker", "market_cap"]].rename(columns={"market_cap": "existing_market_cap"})
    updated = stocks.drop(columns=["market_cap"], errors="ignore").merge(caps, on="ticker", how="left")
    updated = updated.merge(existing_caps, on="ticker", how="left")
    updated["market_cap"] = updated["market_cap"].fillna(updated["existing_market_cap"]).fillna(0)
    count = upsert_rows(conn, "stocks", updated[["ticker", "name", "market", "sector", "industry", "market_cap"]], ["ticker"])
    log_update(conn, "pykrx.market_cap", "success", count, f"{date_yyyymmdd} 시총 업데이트 완료")
    return {"market_cap": count}


def update_dart_corp_codes(conn) -> dict:
    collector = DartCollector()
    corp_codes = collector.fetch_corp_codes()
    if corp_codes.empty:
        log_update(conn, "dart.corp_codes", "failed", 0, "DART corpCode.xml을 가져오지 못했습니다.")
        return {"corp_codes": 0}
    count = upsert_rows(conn, "corp_codes", corp_codes, ["corp_code"])
    log_update(conn, "dart.corp_codes", "success", count, "DART corp_code 매핑 업데이트 완료")
    return {"corp_codes": count}


def update_dart_financials(conn, tickers: list[str] = None, year: int = None, quarter: int = 1, reprt_code: str = "11013") -> dict:
    collector = DartCollector()
    if tickers is None:
        tickers = load_table(conn, "stocks")["ticker"].dropna().head(10).tolist()
    year = year or date.today().year
    corp_codes = load_table(conn, "corp_codes")
    if corp_codes.empty:
        corp_result = update_dart_corp_codes(conn)
        logger.info("corp_codes populated before financial update: %s", corp_result)
        corp_codes = load_table(conn, "corp_codes")
    total = 0
    failed = []
    for ticker in tickers:
        try:
            matched = corp_codes[corp_codes["stock_code"].eq(ticker)]
            if matched.empty:
                raise ValueError(f"corp_code not found in DB for ticker={ticker}")
            raw = collector.fetch_financial_statement_by_corp_code(matched.iloc[0]["corp_code"], year=year, reprt_code=reprt_code)
            financial = collector.normalize_financial_statement(ticker, raw, year=year, quarter=quarter)
            total += upsert_rows(conn, "financials", financial, ["ticker", "year", "quarter"])
        except Exception as error:
            logger.warning("DART financial update failed for %s: %s", ticker, error)
            failed.append(ticker)
    status = "partial" if failed and total else "failed" if failed else "success"
    message = f"실패 {len(failed)}건: {', '.join(failed[:10])}" if failed else f"{year}년 {quarter}분기 재무제표 업데이트 완료"
    log_update(conn, "dart.financials", status, total, message)
    return {"financials": total, "financial_failed": failed}


def update_prices_first_pipeline(conn, tickers: list[str] = None) -> dict:
    result = {}
    result.update(update_stock_master(conn))
    result.update(update_pykrx_prices(conn, tickers=tickers))
    result.update(update_market_caps(conn))
    return result


def update_naver_news(conn, tickers: list[str] = None, display: int = 10) -> dict:
    collector = NaverNewsCollector()
    if not collector.client_id or not collector.client_secret:
        message = (
            "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 .env에서 읽히지 않습니다. "
            "지원 변수명: NAVER_CLIENT_ID/NAVER_CLIENT_SECRET, "
            "NAVER_SEARCH_CLIENT_ID/NAVER_SEARCH_CLIENT_SECRET, "
            "VITE_NAVER_CLIENT_ID/VITE_NAVER_CLIENT_SECRET"
        )
        log_update(conn, "naver.news", "failed", 0, message)
        return {"news": 0, "news_failed": [], "message": message}
    stocks = load_table(conn, "stocks")
    if tickers is not None:
        stocks = stocks[stocks["ticker"].isin(tickers)]
    stocks = stocks.head(20)
    total = 0
    failed = []
    for _, stock_row in stocks.iterrows():
        query = f"{stock_row['name']} {stock_row['sector']}"
        news = collector.search_news(query=query, display=display)
        if news.empty:
            request_hint = f" url={collector.last_request_url}" if collector.last_request_url else ""
            failed.append(f"{stock_row['ticker']}: {collector.last_error or '검색 결과 없음'}{request_hint}")
            continue
        rows = news.assign(
            date=lambda frame: pd.to_datetime(frame["pubDate"], errors="coerce").dt.strftime("%Y-%m-%d").fillna(date.today().isoformat()),
            ticker=stock_row["ticker"],
            source="NAVER",
            url=lambda frame: frame["link"],
            summary=lambda frame: frame["description"],
            keywords=query,
            sentiment=None,
            event_type="NEWS",
        )[["date", "ticker", "title", "source", "url", "summary", "keywords", "sentiment", "event_type"]]
        rows.to_sql("news", conn, if_exists="append", index=False)
        conn.commit()
        total += len(rows)
    status = "partial" if failed and total else "failed" if failed else "success"
    message = f"실패/결과없음 {len(failed)}건: {' | '.join(failed[:5])}" if failed else "NAVER 뉴스 업데이트 완료"
    log_update(conn, "naver.news", status, total, message)
    return {"news": total, "news_failed": failed}


def update_macro_indicators(conn) -> dict:
    macro, failures = collect_macro_indicators_with_diagnostics()
    if macro.empty:
        detail = " | ".join(failures[:8]) if failures else "no diagnostics"
        message = f"Yahoo Finance/pykrx에서 매크로 지표를 가져오지 못했습니다. {detail}"
        log_update(conn, "macro.indicators", "failed", 0, message)
        return {"macro_indicators": 0, "message": message, "failures": failures}
    conn.execute("DELETE FROM macro_indicators WHERE source = 'sample'")
    conn.commit()
    count = upsert_rows(conn, "macro_indicators", macro, ["date", "indicator"])
    status = "partial" if failures else "success"
    message = "Yahoo Finance/pykrx 매크로 지표 업데이트 완료"
    if failures:
        message = f"{message}. 일부 실패: {' | '.join(failures[:5])}"
    log_update(conn, "macro.indicators", status, count, message)
    return {"macro_indicators": count, "failures": failures}


def update_industry_kpis_from_news(conn) -> dict:
    kpis, evidence, failures = collect_industry_kpis_from_news()
    if kpis.empty:
        message = "뉴스에서 산업 KPI 수치를 추출하지 못했습니다."
        if failures:
            message = f"{message} 실패/결과없음: {' | '.join(failures[:5])}"
        log_update(conn, "industry.kpis.news", "failed", 0, message)
        return {"industry_kpis": 0, "evidence": 0, "failures": failures}

    kpi_count = upsert_rows(conn, "industry_kpis", kpis, ["date", "industry", "kpi"])
    evidence.to_sql("industry_kpi_evidence", conn, if_exists="append", index=False)
    conn.commit()
    status = "partial" if failures else "success"
    message = f"NAVER 뉴스 기반 KPI 추출 완료. 실패/결과없음 {len(failures)}건"
    log_update(conn, "industry.kpis.news", status, kpi_count, message)
    return {"industry_kpis": kpi_count, "evidence": len(evidence), "failures": failures}
