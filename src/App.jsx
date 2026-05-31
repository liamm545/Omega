import { useMemo, useState } from "react";
import { Building2, CandlestickChart, HelpCircle, Moon, Sun } from "lucide-react";
import RealEstateDashboard from "./components/RealEstateDashboard.jsx";
import QuizModal from "./components/QuizModal.jsx";
import StockDashboard from "./components/StockDashboard.jsx";

const tabs = [
  { id: "real-estate", label: "Real Estate", icon: Building2 },
  { id: "stock-market", label: "Stock Market", icon: CandlestickChart }
];

export default function App() {
  const [activeTab, setActiveTab] = useState("real-estate");
  const [theme, setTheme] = useState("dark");
  const [isQuizOpen, setIsQuizOpen] = useState(false);

  const isDark = theme === "dark";
  const ActiveTabIcon = useMemo(
    () => tabs.find((tab) => tab.id === activeTab)?.icon ?? Building2,
    [activeTab]
  );

  return (
    <div className={isDark ? "dark" : ""}>
      <div className="min-h-screen bg-finance-soft text-slate-900 transition-colors duration-200 dark:bg-slate-950 dark:text-slate-100">
        <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
          <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-lg bg-finance-blue text-white shadow-dashboard">
                <ActiveTabIcon size={22} />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
                  Personal Study Terminal
                </p>
                <h1 className="text-xl font-bold tracking-normal text-slate-950 dark:text-white">
                  부동산 및 주식 통합 대시보드
                </h1>
              </div>
            </div>

            <nav className="flex flex-wrap items-center gap-2">
              <div className="grid grid-cols-2 rounded-lg border border-slate-200 bg-slate-100 p-1 dark:border-slate-800 dark:bg-slate-900">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;

                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex min-h-10 items-center justify-center gap-2 rounded-md px-3 text-sm font-semibold transition sm:px-4 ${
                        isActive
                          ? "bg-white text-finance-blue shadow-sm dark:bg-slate-800 dark:text-white"
                          : "text-slate-600 hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
                      }`}
                    >
                      <Icon size={17} />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              <button
                type="button"
                onClick={() => setIsQuizOpen(true)}
                className="flex min-h-11 items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 text-sm font-bold text-finance-blue transition hover:border-finance-blue hover:bg-white dark:border-blue-900/70 dark:bg-blue-950/40 dark:text-blue-200 dark:hover:border-finance-blue"
              >
                <HelpCircle size={17} />
                오늘의 퀴즈
              </button>

              <button
                type="button"
                onClick={() => setTheme(isDark ? "light" : "dark")}
                className="flex size-11 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 transition hover:border-finance-blue hover:text-finance-blue dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
                aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
                title={isDark ? "Light mode" : "Dark mode"}
              >
                {isDark ? <Sun size={18} /> : <Moon size={18} />}
              </button>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {activeTab === "real-estate" ? <RealEstateDashboard /> : <StockDashboard />}
        </main>

        <QuizModal isOpen={isQuizOpen} onClose={() => setIsQuizOpen(false)} />
      </div>
    </div>
  );
}
