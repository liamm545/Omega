CREATE TABLE IF NOT EXISTS stocks (
  ticker TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  market TEXT,
  sector TEXT,
  industry TEXT,
  market_cap REAL
);

CREATE TABLE IF NOT EXISTS daily_prices (
  date TEXT NOT NULL,
  ticker TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  trading_value REAL,
  return_1d REAL,
  return_1m REAL,
  return_3m REAL,
  PRIMARY KEY (date, ticker)
);

CREATE TABLE IF NOT EXISTS financials (
  ticker TEXT NOT NULL,
  year INTEGER NOT NULL,
  quarter INTEGER NOT NULL,
  revenue REAL,
  operating_profit REAL,
  net_income REAL,
  assets REAL,
  liabilities REAL,
  equity REAL,
  operating_cash_flow REAL,
  free_cash_flow REAL,
  PRIMARY KEY (ticker, year, quarter)
);

CREATE TABLE IF NOT EXISTS valuation_features (
  date TEXT NOT NULL,
  ticker TEXT NOT NULL,
  per REAL,
  pbr REAL,
  psr REAL,
  ev_ebitda REAL,
  fcf_yield REAL,
  dividend_yield REAL,
  PRIMARY KEY (date, ticker)
);

CREATE TABLE IF NOT EXISTS scores (
  date TEXT NOT NULL,
  ticker TEXT NOT NULL,
  valuation_score REAL,
  quality_score REAL,
  improvement_score REAL,
  momentum_score REAL,
  sector_score REAL,
  event_score REAL,
  risk_penalty REAL,
  total_score REAL,
  grade TEXT,
  PRIMARY KEY (date, ticker)
);

CREATE TABLE IF NOT EXISTS news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT,
  ticker TEXT,
  title TEXT,
  source TEXT,
  url TEXT,
  summary TEXT,
  keywords TEXT,
  sentiment REAL,
  event_type TEXT
);

CREATE TABLE IF NOT EXISTS events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT,
  event_name TEXT,
  related_person TEXT,
  related_company TEXT,
  related_sectors TEXT,
  related_keywords TEXT,
  confidence_score REAL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS event_stock_map (
  event_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  relation_type TEXT,
  relation_strength REAL,
  reason TEXT,
  PRIMARY KEY (event_id, ticker)
);

CREATE TABLE IF NOT EXISTS corp_codes (
  corp_code TEXT PRIMARY KEY,
  corp_name TEXT,
  stock_code TEXT,
  modify_date TEXT
);

CREATE TABLE IF NOT EXISTS filings (
  rcept_no TEXT PRIMARY KEY,
  corp_code TEXT,
  corp_name TEXT,
  stock_code TEXT,
  report_nm TEXT,
  rcept_dt TEXT,
  flr_nm TEXT,
  rm TEXT
);

CREATE TABLE IF NOT EXISTS update_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  source TEXT NOT NULL,
  status TEXT NOT NULL,
  rows INTEGER DEFAULT 0,
  message TEXT
);

CREATE TABLE IF NOT EXISTS macro_indicators (
  date TEXT NOT NULL,
  indicator TEXT NOT NULL,
  name TEXT,
  value REAL,
  unit TEXT,
  change_1d REAL,
  change_1m REAL,
  source TEXT,
  PRIMARY KEY (date, indicator)
);

CREATE TABLE IF NOT EXISTS industry_kpis (
  date TEXT NOT NULL,
  industry TEXT NOT NULL,
  kpi TEXT NOT NULL,
  value REAL,
  unit TEXT,
  change_1m REAL,
  change_3m REAL,
  source TEXT,
  evidence_url TEXT,
  PRIMARY KEY (date, industry, kpi)
);

CREATE TABLE IF NOT EXISTS industry_kpi_evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  collected_at TEXT NOT NULL,
  published_at TEXT,
  industry TEXT NOT NULL,
  kpi TEXT NOT NULL,
  query TEXT,
  value REAL,
  unit TEXT,
  title TEXT,
  url TEXT,
  summary TEXT,
  source TEXT
);

CREATE TABLE IF NOT EXISTS industry_cycle_signals (
  date TEXT NOT NULL,
  industry TEXT NOT NULL,
  cycle_phase TEXT,
  cycle_score REAL,
  confidence REAL,
  key_kpis TEXT,
  positive_evidence TEXT,
  negative_evidence TEXT,
  checkpoints TEXT,
  beneficiaries TEXT,
  risks TEXT,
  PRIMARY KEY (date, industry)
);
