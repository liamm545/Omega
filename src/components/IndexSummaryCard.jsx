import { Line, LineChart, ResponsiveContainer, Tooltip } from "recharts";

const numberFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 2
});

export default function IndexSummaryCard({ item }) {
  const isUp = item.change >= 0;
  const tone = isUp ? "text-red-500" : "text-blue-500";

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{item.symbol}</p>
          <h3 className="mt-1 text-xl font-bold text-slate-950 dark:text-white">{item.name}</h3>
          <p className="mt-3 text-3xl font-bold tabular-nums">
            {numberFormatter.format(item.current)}
          </p>
          <p className={`mt-1 text-sm font-bold tabular-nums ${tone}`}>
            {isUp ? "+" : ""}
            {numberFormatter.format(item.change)} ({isUp ? "+" : ""}
            {item.changeRate.toFixed(2)}%)
          </p>
        </div>

        <div className="h-24 min-w-0 flex-1 sm:max-w-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={item.sparkline}>
              <Tooltip
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #d6dde8",
                  fontSize: 12
                }}
                formatter={(value) => numberFormatter.format(value)}
                labelFormatter={(label) => `${label}`}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={isUp ? "#ef4444" : "#3b82f6"}
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </article>
  );
}
