const API_KEY =
  import.meta.env.VITE_PUBLIC_DATA_SERVICE_KEY || "YOUR_PUBLIC_DATA_PORTAL_SERVICE_KEY_HERE";
const API_URL =
  "/api/1613000/RTMSDataSvcAptTrade";
const PLACEHOLDER_KEY = "YOUR_PUBLIC_DATA_PORTAL_SERVICE_KEY_HERE";
const CACHE_TTL_MS = 30 * 60 * 1000;

console.log("Public Data API Key:", import.meta.env.VITE_PUBLIC_DATA_SERVICE_KEY);

function ensureApiKey() {
  if (!API_KEY || API_KEY === PLACEHOLDER_KEY) {
    throw new Error(
      "공공데이터포털 서비스키가 필요합니다. .env 파일에 VITE_PUBLIC_DATA_SERVICE_KEY=your_key_here 를 추가한 뒤 dev 서버를 재시작하세요."
    );
  }
}

function cacheKey(lawdCode, months) {
  return `finance-study-dashboard:apt-trade:${lawdCode}:${months.join("-")}`;
}

function readCache(key) {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return null;
    const cache = JSON.parse(raw);
    return Date.now() - cache.cachedAt < CACHE_TTL_MS ? cache.data : null;
  } catch {
    return null;
  }
}

function writeCache(key, data) {
  try {
    window.localStorage.setItem(key, JSON.stringify({ cachedAt: Date.now(), data }));
  } catch {
    // If localStorage is unavailable, the API response can still render normally.
  }
}

function lastMonths(count) {
  const now = new Date();

  return Array.from({ length: count }, (_, index) => {
    const date = new Date(now.getFullYear(), now.getMonth() - index, 1);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    return `${year}${month}`;
  }).reverse();
}

function textContent(item, tagName) {
  return item.getElementsByTagName(tagName)[0]?.textContent?.trim() ?? "";
}

function parseAmount(value) {
  return Number(value.replaceAll(",", "").replaceAll(" ", ""));
}

function parseTradeItems(xmlText, month) {
  const xml = new DOMParser().parseFromString(xmlText, "application/xml");
  const errorNode = xml.querySelector("parsererror");

  if (errorNode) {
    console.error("Public Data XML Parse Error:", xmlText);
    throw new Error("실거래가 API 응답 XML을 해석하지 못했습니다.");
  }

  const resultCode = xml.querySelector("resultCode")?.textContent;
  const resultMessage = xml.querySelector("resultMsg")?.textContent;

  if (resultCode && resultCode !== "00") {
    console.error("Public Data API XML Error:", {
      resultCode,
      resultMessage,
      body: xmlText
    });
    throw new Error(resultMessage || `공공데이터포털 오류 코드: ${resultCode}`);
  }

  return Array.from(xml.getElementsByTagName("item")).map((item) => {
    const dealYear = textContent(item, "dealYear");
    const dealMonth = textContent(item, "dealMonth").padStart(2, "0");
    const dealDay = textContent(item, "dealDay").padStart(2, "0");
    const amount = parseAmount(textContent(item, "dealAmount"));

    return {
      month,
      date: `${dealYear}-${dealMonth}-${dealDay}`,
      complexName: textContent(item, "aptNm") || textContent(item, "aptName"),
      legalDong: textContent(item, "umdNm") || textContent(item, "법정동"),
      exclusiveArea: Number(textContent(item, "excluUseAr")),
      floor: textContent(item, "floor"),
      amount
    };
  });
}

async function fetchMonthlyTrades(lawdCd, dealYmd) {
  ensureApiKey();

  const baseUrl = API_URL;
  const serviceKey = API_KEY;
  const url = `${baseUrl}?serviceKey=${serviceKey}&LAWD_CD=${lawdCd}&DEAL_YMD=${dealYmd}&pageNo=1&numOfRows=10`;

  console.log("최종 호출 URL:", url);

  const response = await fetch(url);
  const responseText = await response.text();

  if (!response.ok) {
    console.error("Public Data HTTP Error:", {
      status: response.status,
      statusText: response.statusText,
      body: responseText
    });
    throw new Error(`실거래가 API 요청 실패: HTTP ${response.status} ${response.statusText}`);
  }

  return parseTradeItems(responseText, dealYmd);
}

function summarizeTrades(trades, months) {
  const trend = months.map((month) => {
    const monthTrades = trades.filter((trade) => trade.month === month);
    const average = monthTrades.length
      ? monthTrades.reduce((sum, trade) => sum + trade.amount, 0) / monthTrades.length
      : 0;

    return {
      month: `${month.slice(2, 4)}.${month.slice(4)}`,
      averageAmount: Math.round(average),
      count: monthTrades.length
    };
  });

  const complexes = Array.from(
    trades.reduce((acc, trade) => {
      const name = trade.complexName || "단지명 미상";
      const current = acc.get(name) ?? { name, count: 0, totalAmount: 0, recentDate: trade.date };
      current.count += 1;
      current.totalAmount += trade.amount;
      current.recentDate = trade.date > current.recentDate ? trade.date : current.recentDate;
      acc.set(name, current);
      return acc;
    }, new Map()).values()
  )
    .map((complex) => ({
      ...complex,
      averageAmount: Math.round(complex.totalAmount / complex.count)
    }))
    .sort((a, b) => b.count - a.count || b.averageAmount - a.averageAmount)
    .slice(0, 5);

  return {
    trend,
    complexes,
    totalTrades: trades.length,
    recentTrades: trades
      .slice()
      .sort((a, b) => b.date.localeCompare(a.date))
      .slice(0, 5)
  };
}

export async function fetchApartmentTrades({ lawdCode }) {
  const months = lastMonths(6);
  const key = cacheKey(lawdCode, months);
  const cached = readCache(key);

  if (cached) {
    return { ...cached, source: "cache" };
  }

  const monthlyTrades = await Promise.all(months.map((month) => fetchMonthlyTrades(lawdCode, month)));
  const trades = monthlyTrades.flat();
  const data = {
    ...summarizeTrades(trades, months),
    months,
    source: "api",
    fetchedAt: Date.now()
  };

  writeCache(key, data);
  return data;
}
