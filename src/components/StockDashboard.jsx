import { ExternalLink, Radar, ShieldCheck, Workflow } from "lucide-react";

const modules = [
  {
    title: "Daily Briefing",
    description: "시장 요약, 강한 섹터, 저평가 후보, 이벤트 수혜 후보 볼 수 있음",
    icon: Radar
  },
  {
    title: "Event Radar",
    description: "뉴스/공시/인물/정책 이벤트가 실적 연결 가능성으로 이어지는지 점수화 (점수화 공식 테스트 필요)",
    icon: Workflow
  },
  {
    title: "Research Guardrails",
    description: "자동매매가 아니라 후보군 압축, 투자 가설, 리스크 체크리스트 생성을 목표로!!",
    icon: ShieldCheck
  }
];

export default function StockDashboard() {
  const researchOsUrl = import.meta.env.VITE_INVESTMENT_RADAR_URL || "https://www.yeongyeong.online";

  return (
    <section className="space-y-5">
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
          Stock Market
        </p>
        <h2 className="mt-2 text-2xl font-bold text-slate-950 dark:text-white">
          Investment Radar MVP
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          ㄱㄱ해보자
        </p>
        <a
          href={researchOsUrl}
          target="_blank"
          rel="noreferrer"
          className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-lg bg-finance-blue px-4 text-sm font-bold text-white transition hover:bg-blue-600"
        >
          <ExternalLink size={17} />
          Streamlit Research OS 열기
        </a>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {modules.map((module) => {
          const Icon = module.icon;

          return (
            <article
              key={module.title}
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex size-10 items-center justify-center rounded-lg bg-blue-50 text-finance-blue dark:bg-blue-950/50">
                <Icon size={20} />
              </div>
              <h3 className="mt-4 text-lg font-bold text-slate-950 dark:text-white">{module.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{module.description}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
