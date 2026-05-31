import { useMemo, useState } from "react";
import { CheckCircle2, HelpCircle, X } from "lucide-react";

const quizzes = [
  {
    question: "용적률과 건폐율의 차이를 가장 잘 설명한 것은?",
    options: [
      "용적률은 대지면적 대비 연면적, 건폐율은 대지면적 대비 건축면적이다.",
      "용적률은 전용면적 비율, 건폐율은 공용면적 비율이다.",
      "용적률은 세대 수, 건폐율은 주차 대수를 의미한다."
    ],
    answerIndex: 0,
    explanation:
      "용적률은 땅 위에 얼마나 많은 연면적을 올릴 수 있는지, 건폐율은 땅을 건물이 얼마나 덮는지를 보는 지표입니다."
  },
  {
    question: "취득세를 공부할 때 가장 먼저 확인해야 하는 기준은?",
    options: [
      "매수자의 주택 수, 취득가액, 조정대상지역 여부",
      "아파트 브랜드와 준공 연도",
      "주변 학원가 개수"
    ],
    answerIndex: 0,
    explanation:
      "취득세는 주택 수, 취득가액, 지역 규제 여부 등에 따라 세율이 달라지므로 매수 전 조건을 먼저 정리해야 합니다."
  },
  {
    question: "실거래가를 볼 때 거래량이 중요한 이유는?",
    options: [
      "가격 흐름의 신뢰도와 시장 참여 강도를 같이 판단할 수 있기 때문이다.",
      "거래량이 많으면 반드시 가격이 하락하기 때문이다.",
      "거래량은 세대 수와 항상 같기 때문이다."
    ],
    answerIndex: 0,
    explanation:
      "거래가 적은 가격은 일시적일 수 있습니다. 거래량을 함께 보면 해당 가격대가 시장에서 반복적으로 확인되는지 판단하기 좋습니다."
  }
];

export default function QuizModal({ isOpen, onClose }) {
  const [selectedIndex, setSelectedIndex] = useState(null);
  const quiz = useMemo(() => quizzes[new Date().getDate() % quizzes.length], []);

  if (!isOpen) return null;

  const isAnswered = selectedIndex !== null;
  const isCorrect = selectedIndex === quiz.answerIndex;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-lg border border-slate-700 bg-white p-5 shadow-dashboard dark:bg-slate-900">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="flex items-center gap-2 text-sm font-bold text-finance-blue">
              <HelpCircle size={17} />
              오늘의 부동산 퀴즈
            </p>
            <h2 className="mt-3 text-xl font-bold text-slate-950 dark:text-white">{quiz.question}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex size-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition hover:border-finance-blue hover:text-finance-blue dark:border-slate-700 dark:text-slate-300"
            aria-label="퀴즈 닫기"
          >
            <X size={17} />
          </button>
        </div>

        <div className="mt-5 grid gap-2">
          {quiz.options.map((option, index) => {
            const isSelected = selectedIndex === index;
            const isAnswer = quiz.answerIndex === index;

            return (
              <button
                key={option}
                type="button"
                onClick={() => setSelectedIndex(index)}
                className={`rounded-lg border p-3 text-left text-sm font-semibold leading-6 transition ${
                  isAnswered && isAnswer
                    ? "border-emerald-400 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200"
                    : isSelected
                      ? "border-blue-400 bg-blue-50 text-finance-blue dark:bg-blue-950/40"
                      : "border-slate-200 text-slate-700 hover:border-finance-blue dark:border-slate-700 dark:text-slate-200"
                }`}
              >
                {option}
              </button>
            );
          })}
        </div>

        {isAnswered ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950">
            <p className={`flex items-center gap-2 text-sm font-bold ${isCorrect ? "text-emerald-500" : "text-blue-500"}`}>
              <CheckCircle2 size={16} />
              {isCorrect ? "정답입니다. 오늘의 공부 완료!" : "조금 아쉽지만 핵심은 잡았습니다."}
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{quiz.explanation}</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
