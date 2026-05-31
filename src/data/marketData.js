// Alpha Vantage configuration.
// 1. Get a free key: https://www.alphavantage.co/support/#api-key
// 2. Create `.env` in the project root and add:
//    VITE_ALPHA_VANTAGE_API_KEY=your_key_here
// 3. Restart `npm run dev`.
//
// You may also replace the placeholder below for quick local testing, but `.env`
// is safer because it keeps your key out of committed source code.
// Optional: set VITE_ALPHA_VANTAGE_USE_BULK_QUOTES=true to try the Bulk Quotes
// endpoint for US tickers. Keep it false/empty on the free GLOBAL_QUOTE path.
export const ALPHA_VANTAGE_API_KEY =
  import.meta.env.VITE_ALPHA_VANTAGE_API_KEY || "1350MI3YK6ZDHD80";

export const ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query";

// Alpha Vantage has dedicated INDEX_DATA support for Nasdaq Composite as `COMP`.
// KOSPI support can vary by data entitlement and symbol catalog. If your key
// returns an empty result for KOSPI, use the Index Catalog/Search utilities in
// Alpha Vantage and update only this symbol.
export const indexRequests = [
  { symbol: "KOSPI", apiSymbol: "KOSPI", name: "코스피", interval: "daily" },
  { symbol: "NASDAQ", apiSymbol: "COMP", name: "나스닥", interval: "daily" }
];

// `apiSymbol` is the provider ticker. Korean tickers may differ by provider.
// If Alpha Vantage returns "Invalid API call" for a Korean listing, search the
// provider symbol and update this config without touching the table component.
export const stockRequests = [
  { symbol: "005930", apiSymbol: "005930.KS", name: "삼성전자" },
  { symbol: "000660", apiSymbol: "000660.KS", name: "SK하이닉스" },
  { symbol: "035420", apiSymbol: "035420.KS", name: "NAVER" },
  { symbol: "AAPL", apiSymbol: "AAPL", name: "Apple" },
  { symbol: "NVDA", apiSymbol: "NVDA", name: "NVIDIA" },
  { symbol: "TSLA", apiSymbol: "TSLA", name: "Tesla" }
];
