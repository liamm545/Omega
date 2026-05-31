import {
  ALPHA_VANTAGE_API_KEY,
  ALPHA_VANTAGE_BASE_URL,
  indexRequests,
  stockRequests
} from "../data/marketData.js";

const PLACEHOLDER_KEY = "YOUR_ALPHA_VANTAGE_API_KEY_HERE";
const CACHE_KEY = "finance-study-dashboard:alpha-vantage:v1";
const CACHE_TTL_MS = 15 * 60 * 1000;

let inFlightDashboardRequest = null;

console.log("Stock API Key:", import.meta.env.VITE_ALPHA_VANTAGE_API_KEY);

function readCachedDashboardData() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const rawCache = window.localStorage.getItem(CACHE_KEY);
    if (!rawCache) {
      return null;
    }

    const cache = JSON.parse(rawCache);
    const isFresh = Date.now() - cache.cachedAt < CACHE_TTL_MS;

    return isFresh ? cache : null;
  } catch {
    return null;
  }
}

function readAnyCachedDashboardData() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const rawCache = window.localStorage.getItem(CACHE_KEY);
    return rawCache ? JSON.parse(rawCache) : null;
  } catch {
    return null;
  }
}

function writeCachedDashboardData(data) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(
      CACHE_KEY,
      JSON.stringify({
        ...data,
        cachedAt: Date.now(),
        source: "api"
      })
    );
  } catch {
    // localStorage can fail in private mode or quota-limited browsers.
    // The dashboard still works; it simply falls back to live requests.
  }
}

function ensureApiKey() {
  if (!ALPHA_VANTAGE_API_KEY || ALPHA_VANTAGE_API_KEY === PLACEHOLDER_KEY) {
    throw new Error(
      "Alpha Vantage API 키가 필요합니다. 프로젝트 루트의 .env 파일에 VITE_ALPHA_VANTAGE_API_KEY=your_key_here 를 추가한 뒤 dev 서버를 재시작하세요."
    );
  }
}

async function requestAlphaVantage(params) {
  ensureApiKey();

  const url = new URL(ALPHA_VANTAGE_BASE_URL);
  Object.entries({ ...params, apikey: ALPHA_VANTAGE_API_KEY }).forEach(([key, value]) => {
    url.searchParams.set(key, value);
  });

  const response = await fetch(url);
  const responseText = await response.text();

  if (!response.ok) {
    console.error("Alpha Vantage HTTP Error:", {
      status: response.status,
      statusText: response.statusText,
      body: responseText
    });
    throw new Error(`Alpha Vantage 요청 실패: HTTP ${response.status} ${response.statusText}`);
  }

  let payload;
  try {
    payload = JSON.parse(responseText);
  } catch (error) {
    console.error("Alpha Vantage JSON Parse Error:", {
      message: error.message,
      body: responseText
    });
    throw new Error("Alpha Vantage 응답을 JSON으로 해석하지 못했습니다.");
  }

  if (payload.Note || payload.Information) {
    console.error("Alpha Vantage API Message:", payload);
    throw new Error(payload.Note || payload.Information);
  }

  if (payload["Error Message"]) {
    console.error("Alpha Vantage API Error:", payload);
    throw new Error(payload["Error Message"]);
  }

  return payload;
}

function parseBulkQuoteRow(row, fallback) {
  const current = Number(row.price ?? row.close ?? row["05. price"] ?? 0);
  const change = Number(row.change ?? row["09. change"] ?? 0);
  const changeRate = parsePercent(row.change_percent ?? row.changePercent ?? row["10. change percent"]);

  return {
    symbol: fallback.symbol,
    apiSymbol: fallback.apiSymbol,
    name: fallback.name,
    current,
    price: current,
    change,
    changeRate,
    volume: Number(row.volume ?? row["06. volume"] ?? 0)
  };
}

function parsePercent(value) {
  return Number(String(value ?? "0").replace("%", ""));
}

function parseGlobalQuote(payload, fallback) {
  const quote = payload["Global Quote"];

  if (!quote || Object.keys(quote).length === 0) {
    throw new Error(`${fallback.name} quote 데이터가 비어 있습니다. provider 심볼(${fallback.apiSymbol})을 확인하세요.`);
  }

  return {
    symbol: fallback.symbol,
    apiSymbol: fallback.apiSymbol,
    name: fallback.name,
    current: Number(quote["05. price"]),
    price: Number(quote["05. price"]),
    change: Number(quote["09. change"]),
    changeRate: parsePercent(quote["10. change percent"]),
    volume: Number(quote["06. volume"] ?? 0)
  };
}

function parseIndexSeries(payload, fallback) {
  const series = payload.data;

  if (!Array.isArray(series) || series.length < 2) {
    throw new Error(`${fallback.name} 지수 데이터가 비어 있습니다. provider 심볼(${fallback.apiSymbol})을 확인하세요.`);
  }

  const latest = series[0];
  const previous = series[1];
  const current = Number(latest.close);
  const previousClose = Number(previous.close);
  const change = current - previousClose;

  return {
    symbol: fallback.symbol,
    apiSymbol: fallback.apiSymbol,
    name: fallback.name,
    current,
    change,
    changeRate: previousClose ? (change / previousClose) * 100 : 0,
    sparkline: series
      .slice(0, 20)
      .reverse()
      .map((point) => ({
        time: point.date,
        value: Number(point.close)
      }))
  };
}

async function fetchIndexSummary(request) {
  const payload = await requestAlphaVantage({
    function: "INDEX_DATA",
    symbol: request.apiSymbol,
    interval: request.interval
  });

  return parseIndexSeries(payload, request);
}

async function fetchStockQuote(request) {
  const payload = await requestAlphaVantage({
    function: "GLOBAL_QUOTE",
    symbol: request.apiSymbol
  });

  return parseGlobalQuote(payload, request);
}

async function fetchBulkStockQuotes(requests) {
  const payload = await requestAlphaVantage({
    function: "REALTIME_BULK_QUOTES",
    symbol: requests.map((request) => request.apiSymbol).join(",")
  });

  const rows = payload.data ?? payload["data"];
  if (!Array.isArray(rows)) {
    throw new Error("Bulk quote 데이터가 비어 있습니다. 무료 키에서는 GLOBAL_QUOTE 개별 요청 경로를 사용하세요.");
  }

  const rowsBySymbol = new Map(rows.map((row) => [row.symbol, row]));

  return requests.map((request) => {
    const row = rowsBySymbol.get(request.apiSymbol);
    if (!row) {
      throw new Error(`${request.name} bulk quote 데이터가 없습니다.`);
    }

    return parseBulkQuoteRow(row, request);
  });
}

async function fetchStockQuotesEfficiently() {
  const useBulkQuotes = import.meta.env.VITE_ALPHA_VANTAGE_USE_BULK_QUOTES === "true";

  if (!useBulkQuotes) {
    return Promise.all(stockRequests.map(fetchStockQuote));
  }

  // Alpha Vantage Bulk Quotes accepts comma-separated tickers, but it is a
  // separate endpoint from the free GLOBAL_QUOTE path. Keep Korean exchange
  // symbols on the standard endpoint and batch US symbols only when enabled.
  const bulkRequests = stockRequests.filter((request) => !request.apiSymbol.includes("."));
  const individualRequests = stockRequests.filter((request) => request.apiSymbol.includes("."));
  const [bulkResults, individualResults] = await Promise.all([
    bulkRequests.length ? fetchBulkStockQuotes(bulkRequests) : Promise.resolve([]),
    Promise.all(individualRequests.map(fetchStockQuote))
  ]);
  const resultBySymbol = new Map(
    [...bulkResults, ...individualResults].map((result) => [result.symbol, result])
  );

  return stockRequests.map((request) => resultBySymbol.get(request.symbol));
}

async function fetchFreshMarketDashboardData() {
  const [indexes, stocks] = await Promise.all([
    Promise.all(indexRequests.map(fetchIndexSummary)),
    fetchStockQuotesEfficiently()
  ]);

  return { indexes, stocks };
}

export async function fetchMarketDashboardData({ forceRefresh = false } = {}) {
  if (!forceRefresh) {
    const cachedData = readCachedDashboardData();
    if (cachedData) {
      return { ...cachedData, source: "cache" };
    }
  }

  if (inFlightDashboardRequest) {
    return inFlightDashboardRequest;
  }

  inFlightDashboardRequest = fetchFreshMarketDashboardData()
    .then((data) => {
      writeCachedDashboardData(data);
      return { ...data, cachedAt: Date.now(), source: "api" };
    })
    .catch((error) => {
      const staleCache = readAnyCachedDashboardData();
      if (staleCache) {
        return {
          ...staleCache,
          source: "stale-cache",
          warning: `API 요청 실패로 저장된 데이터를 표시합니다. ${error.message}`
        };
      }

      throw error;
    })
    .finally(() => {
      inFlightDashboardRequest = null;
    });

  return inFlightDashboardRequest;
}
