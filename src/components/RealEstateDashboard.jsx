import { useEffect, useMemo, useState } from "react";
import {
  Building,
  CheckCircle2,
  Loader2,
  MapPin,
  Save,
  TrendingUp
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import SeoulMap from "./SeoulMap.jsx";
import MetricCard from "./MetricCard.jsx";
import { fetchApartmentTrades } from "../api/realEstate.js";
import { seoulDistricts } from "../data/seoulDistricts.js";

const amountFormatter = new Intl.NumberFormat("ko-KR");

function formatAmount(amountInManwon) {
  if (!amountInManwon) return "-";
  return `${(amountInManwon / 10000).toFixed(1)}억`;
}

function memoKey(districtId) {
  return `finance-study-dashboard:real-estate-memo:${districtId}`;
}

export default function RealEstateDashboard() {
  const [selectedDistrictId, setSelectedDistrictId] = useState("gangnam-gu");
  const [tradeData, setTradeData] = useState(null);
  const [tradeStatus, setTradeStatus] = useState("loading");
  const [tradeError, setTradeError] = useState("");
  const [memo, setMemo] = useState("");
  const [memoSaved, setMemoSaved] = useState(false);

  const selectedDistrict = useMemo(
    () => seoulDistricts.find((district) => district.id === selectedDistrictId),
    [selectedDistrictId]
  );

  useEffect(() => {
    if (!selectedDistrict?.lawdCode) return;

    let isCurrent = true;
    setTradeStatus("loading");
    setTradeError("");

    fetchApartmentTrades({ lawdCode: selectedDistrict.lawdCode })
      .then((data) => {
        if (!isCurrent) return;
        setTradeData(data);
        setTradeStatus("success");
      })
      .catch((error) => {
        if (!isCurrent) return;
        setTradeError(error.message);
        setTradeData(null);
        setTradeStatus("error");
      });

    return () => {
      isCurrent = false;
    };
  }, [selectedDistrict]);

  useEffect(() => {
    setMemo(window.localStorage.getItem(memoKey(selectedDistrictId)) ?? "");
    setMemoSaved(false);
  }, [selectedDistrictId]);

  const handleSaveMemo = () => {
    window.localStorage.setItem(memoKey(selectedDistrictId), memo);
    setMemoSaved(true);
    window.setTimeout(() => setMemoSaved(false), 1800);
  };

  const handleSelectDistrict = (districtId) => {
    setSelectedDistrictId(districtId);
  };

  return (
    <section className="space-y-5">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Coverage" value="서울 25개구" caption="자치구별 실거래/단지 학습" />
        <MetricCard label="Selected" value={selectedDistrict?.name ?? "-"} caption={selectedDistrict?.lawdCode ?? "-"} />
        <MetricCard
          label="Trade Count"
          value={tradeData ? amountFormatter.format(tradeData.totalTrades) : "-"}
          caption={tradeData?.source === "cache" ? "저장된 실거래 데이터" : "최근 6개월 조회"}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
        <SeoulMap selectedDistrictId={selectedDistrictId} onSelectDistrict={handleSelectDistrict} />

        <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="flex items-center gap-2 text-sm font-semibold text-finance-blue">
                <MapPin size={16} />
                Selected District
              </p>
              <h2 className="mt-2 text-2xl font-bold text-slate-950 dark:text-white">
                {selectedDistrict?.name}
              </h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                법정동 코드 {selectedDistrict?.lawdCode}
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/70">
              <p className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                <TrendingUp size={16} />
                최근 실거래가 추이
              </p>

              {tradeStatus === "loading" ? (
                <div className="mt-4 flex h-52 flex-col items-center justify-center rounded-md bg-white text-sm font-semibold text-finance-blue dark:bg-slate-900">
                  <Loader2 className="mb-3 animate-spin" size={24} />
                  데이터 분석 중...
                </div>
              ) : tradeStatus === "error" ? (
                <div className="mt-4 rounded-md border border-blue-200 bg-white p-4 text-sm leading-6 text-blue-700 dark:border-blue-900 dark:bg-slate-900 dark:text-blue-200">
                  {tradeError}
                </div>
              ) : (
                <div className="mt-4 h-52 rounded-md bg-white p-3 dark:bg-slate-900">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={tradeData.trend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#d6dde8" />
                      <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                      <YAxis
                        tick={{ fontSize: 11 }}
                        tickFormatter={(value) => `${Math.round(value / 10000)}억`}
                        width={44}
                      />
                      <Tooltip
                        formatter={(value, name) => [
                          name === "averageAmount" ? formatAmount(value) : value,
                          name === "averageAmount" ? "평균 거래가" : "거래 건수"
                        ]}
                        labelFormatter={(label) => `20${label}`}
                      />
                      <Line
                        type="monotone"
                        dataKey="averageAmount"
                        stroke="#007bff"
                        strokeWidth={3}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
              <p className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                <Building size={16} />
                거래 활발 단지 TOP 5
              </p>
              {tradeStatus === "loading" ? (
                <div className="mt-4 flex h-28 items-center justify-center text-sm font-semibold text-finance-blue">
                  <Loader2 className="mr-2 animate-spin" size={18} />
                  데이터 분석 중...
                </div>
              ) : tradeStatus === "error" ? (
                <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">API 연결 후 단지 리스트가 표시됩니다.</p>
              ) : (
                <ul className="mt-3 divide-y divide-slate-200 dark:divide-slate-800">
                  {tradeData.complexes.map((complex) => (
                    <li key={complex.name} className="flex items-center justify-between gap-3 py-3 text-sm">
                      <div>
                        <span className="font-medium text-slate-800 dark:text-slate-100">{complex.name}</span>
                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          평균 {formatAmount(complex.averageAmount)} · 최근 {complex.recentDate}
                        </p>
                      </div>
                      <span className="shrink-0 rounded-md bg-blue-50 px-2 py-1 text-xs font-bold text-finance-blue dark:bg-blue-950/50">
                        {complex.count}건
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">나의 분석 메모</p>
                {memoSaved ? (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-500">
                    <CheckCircle2 size={14} />
                    저장됨
                  </span>
                ) : null}
              </div>
              <textarea
                value={memo}
                onChange={(event) => setMemo(event.target.value)}
                rows={5}
                placeholder={`${selectedDistrict?.name}의 입지, 거래량, 관심 단지를 기록해보세요.`}
                className="mt-3 w-full resize-none rounded-lg border border-slate-200 bg-white p-3 text-sm leading-6 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-finance-blue dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              />
              <button
                type="button"
                onClick={handleSaveMemo}
                className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-lg bg-finance-blue px-4 text-sm font-bold text-white transition hover:bg-blue-600"
              >
                <Save size={16} />
                저장
              </button>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
