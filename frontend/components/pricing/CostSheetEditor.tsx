"use client";

/**
 * 산출내역서 편집 시뮬레이터
 *
 * - 스프레드시트형 UI로 인건비·경비·간접비를 실시간 편집
 * - 비목별 비율 조정 모드: 목표 총액 설정 → 비목 비율 슬라이더 → 자동 배분
 * - 직접경비 세부항목: 대항목 → 세부항목 트리 구조
 * - 최종 승인 시 DOCX 생성·다운로드
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  costSheetApi,
  type CostSheetDraft,
  type LaborItem,
  type ExpenseItem,
  type BudgetNarrativeItem,
} from "@/lib/api";

interface Props {
  proposalId: string;
}

// 세부항목이 있는 경비 항목
interface ExpenseGroup {
  name: string;
  subitems: ExpenseItem[];
}

function fmtWon(n: number): string {
  return n.toLocaleString("ko-KR") + "원";
}
function fmtShort(n: number): string {
  if (Math.abs(n) >= 100_000_000) return `${(n / 100_000_000).toFixed(1)}억`;
  if (Math.abs(n) >= 10_000_000) return `${(n / 10_000_000).toFixed(1)}천만`;
  if (Math.abs(n) >= 10_000) return `${(n / 10_000).toFixed(0)}만`;
  return n.toLocaleString();
}

// ── 인건비 행 ──
function LaborRow({
  item,
  index,
  onChange,
  onRemove,
}: {
  item: LaborItem;
  index: number;
  onChange: (i: number, field: keyof LaborItem, value: string | number) => void;
  onRemove: (i: number) => void;
}) {
  return (
    <tr className="border-b border-[#1f1f1f] hover:bg-[#1a1a1a] group">
      <td className="py-1.5 px-2">
        <input
          value={item.grade}
          onChange={(e) => onChange(index, "grade", e.target.value)}
          className="w-full bg-transparent text-xs text-[#ededed] outline-none"
        />
      </td>
      <td className="py-1.5 px-2">
        <input
          value={item.role || ""}
          onChange={(e) => onChange(index, "role", e.target.value)}
          className="w-full bg-transparent text-xs text-[#ededed] outline-none"
        />
      </td>
      <td className="py-1.5 px-2">
        <input
          type="number"
          value={item.monthly_rate}
          onChange={(e) =>
            onChange(index, "monthly_rate", parseInt(e.target.value) || 0)
          }
          className="w-full bg-transparent text-xs text-[#ededed] text-right outline-none font-mono"
        />
      </td>
      <td className="py-1.5 px-2">
        <input
          type="number"
          step="0.5"
          value={item.mm}
          onChange={(e) =>
            onChange(index, "mm", parseFloat(e.target.value) || 0)
          }
          className="w-full bg-transparent text-xs text-[#ededed] text-center outline-none font-mono"
        />
      </td>
      <td className="py-1.5 px-2 text-right text-xs font-mono text-[#ededed]">
        {fmtWon(item.subtotal)}
      </td>
      <td className="py-1.5 px-1 text-center">
        <button
          onClick={() => onRemove(index)}
          className="text-red-400/30 group-hover:text-red-400/70 hover:!text-red-400 text-xs"
        >
          ✕
        </button>
      </td>
    </tr>
  );
}

export default function CostSheetEditor({ proposalId }: Props) {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [meta, setMeta] = useState({
    project_name: "",
    client: "",
    proposer_name: "",
    cost_standard: "KOSA",
  });
  const [labor, setLabor] = useState<LaborItem[]>([]);
  const [expenseGroups, setExpenseGroups] = useState<ExpenseGroup[]>([]);
  const [overheadRate, setOverheadRate] = useState(110); // 정수 % (110 = 110%)
  const [profitRate, setProfitRate] = useState(22); // 정수 % (22 = 22%)
  const [narrative, setNarrative] = useState<BudgetNarrativeItem[]>([]);

  // 비율 조정 모드
  const [ratioMode, setRatioMode] = useState(false);
  const [targetTotal, setTargetTotal] = useState(0);
  const [ratios, setRatios] = useState({
    labor: 60,
    expense: 15,
    overhead: 18,
    profit: 7,
  });

  // ── 초안 로드 ──
  useEffect(() => {
    (async () => {
      try {
        const draft = await costSheetApi.getDraft(proposalId);
        setMeta({
          project_name: draft.project_name,
          client: draft.client,
          proposer_name: draft.proposer_name,
          cost_standard: draft.cost_standard,
        });
        setLabor(
          draft.labor_breakdown.map((l) => ({
            ...l,
            subtotal: l.subtotal || Math.round(l.monthly_rate * l.mm),
          })),
        );
        // 기존 flat 경비를 그룹화 (초기에는 각 항목이 독립 그룹)
        setExpenseGroups(
          draft.expense_items.map((e) => ({ name: e.name, subitems: [e] })),
        );
        if (draft.overhead_rate > 2) {
          setOverheadRate(Math.round((draft.overhead_rate - 1) * 100));
        } else {
          setOverheadRate(Math.round(draft.overhead_rate * 100));
        }
        setProfitRate(Math.round(draft.profit_rate * 100));
        setNarrative(draft.budget_narrative);
        setTargetTotal(draft.total_cost || 0);
      } catch (e) {
        console.error("산출내역서 초안 로드 실패:", e);
      } finally {
        setLoading(false);
      }
    })();
  }, [proposalId]);

  // ── 자동 합계 ──
  const laborTotal = useMemo(
    () => labor.reduce((s, l) => s + l.subtotal, 0),
    [labor],
  );
  const expenseTotal = useMemo(
    () =>
      expenseGroups.reduce(
        (s, g) => s + g.subitems.reduce((ss, e) => ss + e.amount, 0),
        0,
      ),
    [expenseGroups],
  );
  const overheadTotal = Math.round((laborTotal * overheadRate) / 100);
  const profitTotal = Math.round(
    ((laborTotal + overheadTotal) * profitRate) / 100,
  );
  const subtotal = laborTotal + expenseTotal + overheadTotal + profitTotal;
  const vat = Math.round(subtotal * 0.1);
  const grandTotal = subtotal + vat;
  const totalMM = useMemo(() => labor.reduce((s, l) => s + l.mm, 0), [labor]);

  // 비목별 비율 (현재 실제 비율)
  const actualRatios = useMemo(() => {
    const base = subtotal || 1;
    return {
      labor: Math.round((laborTotal / base) * 100),
      expense: Math.round((expenseTotal / base) * 100),
      overhead: Math.round((overheadTotal / base) * 100),
      profit: Math.round((profitTotal / base) * 100),
    };
  }, [laborTotal, expenseTotal, overheadTotal, profitTotal, subtotal]);

  // ── 비율 조정 모드: 슬라이더 → 실제 금액 재배분 ──
  const applyRatioDistribution = useCallback(() => {
    if (!targetTotal || targetTotal <= 0) return;
    const baseAmount = Math.round(targetTotal / 1.1); // VAT 제외 기준
    const newLaborTotal = Math.round((baseAmount * ratios.labor) / 100);
    const newExpenseTotal = Math.round((baseAmount * ratios.expense) / 100);
    const newOverheadPct = ratios.overhead;
    const newProfitPct = ratios.profit;

    // 인건비 비례 조정 (기존 비율 유지하면서 총액 맞춤)
    if (laborTotal > 0 && labor.length > 0) {
      const scale = newLaborTotal / laborTotal;
      setLabor((prev) =>
        prev.map((l) => ({
          ...l,
          mm: Math.round(l.mm * scale * 10) / 10,
          subtotal: Math.round(l.subtotal * scale),
        })),
      );
    }

    // 경비 비례 조정
    if (expenseTotal > 0 && expenseGroups.length > 0) {
      const scale = newExpenseTotal / expenseTotal;
      setExpenseGroups((prev) =>
        prev.map((g) => ({
          ...g,
          subitems: g.subitems.map((e) => ({
            ...e,
            amount: Math.round(e.amount * scale),
          })),
        })),
      );
    }

    // 간접비·기술료율은 직접 반영하기 어려우므로 비율만 업데이트
    // (간접비 = 인건비 × X%이므로, 목표 간접비에서 역산)
    if (newLaborTotal > 0) {
      const targetOverhead = Math.round((baseAmount * newOverheadPct) / 100);
      setOverheadRate(Math.round((targetOverhead / newLaborTotal) * 100));
    }
    const targetLaborPlusOverhead = Math.round(
      (baseAmount * (ratios.labor + ratios.overhead)) / 100,
    );
    if (targetLaborPlusOverhead > 0) {
      const targetProfit = Math.round((baseAmount * newProfitPct) / 100);
      setProfitRate(Math.round((targetProfit / targetLaborPlusOverhead) * 100));
    }
  }, [targetTotal, ratios, laborTotal, expenseTotal, labor, expenseGroups]);

  // ── 인건비 편집 ──
  const handleLaborChange = useCallback(
    (i: number, field: keyof LaborItem, value: string | number) => {
      setLabor((prev) => {
        const next = [...prev];
        const item = { ...next[i], [field]: value };
        if (field === "monthly_rate" || field === "mm") {
          item.subtotal = Math.round(item.monthly_rate * item.mm);
        }
        next[i] = item;
        return next;
      });
    },
    [],
  );
  const addLabor = () =>
    setLabor((p) => [
      ...p,
      {
        grade: "중급",
        role: "",
        monthly_rate: 5_170_000,
        mm: 1,
        subtotal: 5_170_000,
      },
    ]);
  const removeLabor = (i: number) =>
    setLabor((p) => p.filter((_, idx) => idx !== i));

  // ── 경비 그룹 편집 ──
  const addExpenseGroup = () =>
    setExpenseGroups((p) => [
      ...p,
      {
        name: "새 항목",
        subitems: [{ name: "", amount: 0, basis: "" }],
      },
    ]);
  const removeExpenseGroup = (gi: number) =>
    setExpenseGroups((p) => p.filter((_, i) => i !== gi));
  const updateGroupName = (gi: number, name: string) => {
    setExpenseGroups((p) => {
      const n = [...p];
      n[gi] = { ...n[gi], name };
      return n;
    });
  };
  const addSubitem = (gi: number) => {
    setExpenseGroups((p) => {
      const n = [...p];
      n[gi] = {
        ...n[gi],
        subitems: [...n[gi].subitems, { name: "", amount: 0, basis: "" }],
      };
      return n;
    });
  };
  const removeSubitem = (gi: number, si: number) => {
    setExpenseGroups((p) => {
      const n = [...p];
      n[gi] = { ...n[gi], subitems: n[gi].subitems.filter((_, i) => i !== si) };
      if (n[gi].subitems.length === 0) return n.filter((_, i) => i !== gi);
      return n;
    });
  };
  const updateSubitem = (
    gi: number,
    si: number,
    field: keyof ExpenseItem,
    value: string | number,
  ) => {
    setExpenseGroups((p) => {
      const n = [...p];
      const subs = [...n[gi].subitems];
      subs[si] = { ...subs[si], [field]: value };
      n[gi] = { ...n[gi], subitems: subs };
      return n;
    });
  };

  // ── flat 경비 목록 (API용) ──
  const flatExpenses: ExpenseItem[] = useMemo(
    () =>
      expenseGroups.flatMap((g) =>
        g.subitems.map((s) => ({
          name:
            g.subitems.length > 1 ? `${g.name} - ${s.name}` : s.name || g.name,
          amount: s.amount,
          basis: s.basis,
        })),
      ),
    [expenseGroups],
  );

  // ── DOCX 생성 ──
  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const blob = await costSheetApi.generate(proposalId, {
        project_name: meta.project_name,
        client: meta.client,
        proposer_name: meta.proposer_name,
        cost_standard: meta.cost_standard,
        labor_breakdown: labor,
        expense_items: flatExpenses,
        overhead_rate: 1 + overheadRate / 100,
        profit_rate: profitRate / 100,
        budget_narrative: narrative,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${meta.project_name || "제안서"}_산출내역서.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(e instanceof Error ? e.message : "산출내역서 생성 실패");
    } finally {
      setGenerating(false);
    }
  };

  if (loading)
    return (
      <div className="text-sm text-[#8c8c8c] p-4">
        산출내역서 초안 로딩 중...
      </div>
    );

  return (
    <div className="space-y-4">
      {/* ═══ 헤더 ═══ */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-[#ededed]">
            산출내역서 편집
          </h2>
          <p className="text-xs text-[#8c8c8c] mt-0.5">
            항목을 수정하면 합계가 자동 재계산됩니다
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setRatioMode((v) => !v)}
            className={`text-[10px] px-2.5 py-1 rounded border transition-colors ${
              ratioMode
                ? "border-[#3ecf8e]/50 bg-[#3ecf8e]/10 text-[#3ecf8e]"
                : "border-[#333] bg-[#161616] text-[#8c8c8c] hover:text-[#ededed]"
            }`}
          >
            비율 조정
          </button>
          <span className="text-xs text-[#8c8c8c]">
            {meta.cost_standard} · {totalMM.toFixed(1)}MM
          </span>
        </div>
      </div>

      {/* ═══ 비율 조정 모드 ═══ */}
      {ratioMode && (
        <div className="rounded-lg border border-[#3ecf8e]/20 bg-[#3ecf8e]/5 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-medium text-[#3ecf8e]">
              비목별 비율 조정
            </h3>
            <div className="flex items-center gap-2">
              <label className="text-[10px] text-[#8c8c8c]">
                목표 총액 (VAT 포함)
              </label>
              <input
                type="number"
                value={targetTotal}
                onChange={(e) => setTargetTotal(parseInt(e.target.value) || 0)}
                className="w-36 px-2 py-1 bg-[#0a0a0a] border border-[#333] rounded text-xs text-[#ededed] text-right font-mono focus:border-[#3ecf8e] outline-none"
              />
            </div>
          </div>

          {/* 비율 슬라이더 */}
          <div className="grid grid-cols-4 gap-3">
            {[
              {
                key: "labor" as const,
                label: "직접인건비",
                color: "bg-blue-400",
              },
              {
                key: "expense" as const,
                label: "직접경비",
                color: "bg-amber-400",
              },
              {
                key: "overhead" as const,
                label: "간접비",
                color: "bg-purple-400",
              },
              {
                key: "profit" as const,
                label: "기술료",
                color: "bg-green-400",
              },
            ].map(({ key, label, color }) => (
              <div key={key}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-[#8c8c8c]">{label}</span>
                  <span className="text-xs font-mono text-[#ededed]">
                    {ratios[key]}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="80"
                  value={ratios[key]}
                  onChange={(e) =>
                    setRatios((p) => ({
                      ...p,
                      [key]: parseInt(e.target.value),
                    }))
                  }
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-[#3ecf8e]"
                  style={{
                    background: `linear-gradient(to right, ${color.replace("bg-", "rgb(")}, 50%) ${ratios[key]}%, #262626 ${ratios[key]}%)`,
                  }}
                />
                <div className="flex justify-between text-[9px] text-[#555] mt-0.5">
                  <span>현재 {actualRatios[key]}%</span>
                  <span>
                    {targetTotal > 0
                      ? fmtShort(
                          Math.round(((targetTotal / 1.1) * ratios[key]) / 100),
                        )
                      : "—"}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[#8c8c8c]">
              합계:{" "}
              {ratios.labor + ratios.expense + ratios.overhead + ratios.profit}%
              {ratios.labor +
                ratios.expense +
                ratios.overhead +
                ratios.profit !==
                100 && (
                <span className="text-amber-400 ml-1">(100%가 아님)</span>
              )}
            </span>
            <button
              onClick={applyRatioDistribution}
              disabled={
                !targetTotal ||
                ratios.labor +
                  ratios.expense +
                  ratios.overhead +
                  ratios.profit ===
                  0
              }
              className="px-3 py-1 rounded text-[10px] font-medium bg-[#3ecf8e] text-[#0a0a0a] hover:bg-[#3ecf8e]/90 disabled:opacity-50 transition-colors"
            >
              비율 적용
            </button>
          </div>
        </div>
      )}

      {/* ═══ 총괄 요약 ═══ */}
      <div className="grid grid-cols-5 gap-2">
        {[
          { label: "직접인건비", value: laborTotal, pct: actualRatios.labor },
          { label: "직접경비", value: expenseTotal, pct: actualRatios.expense },
          { label: "간접비", value: overheadTotal, pct: actualRatios.overhead },
          { label: "기술료", value: profitTotal, pct: actualRatios.profit },
          { label: "합계(VAT)", value: grandTotal, pct: 0 },
        ].map(({ label, value, pct }) => (
          <div
            key={label}
            className="rounded-lg border border-[#262626] bg-[#161616] p-3 text-center"
          >
            <p className="text-[10px] text-[#8c8c8c]">{label}</p>
            <p
              className={`text-sm font-mono font-medium mt-1 ${label.includes("합계") ? "text-[#3ecf8e]" : "text-[#ededed]"}`}
            >
              {fmtShort(value)}
            </p>
            {pct > 0 && <p className="text-[9px] text-[#555] mt-0.5">{pct}%</p>}
          </div>
        ))}
      </div>

      {/* ═══ 1. 직접인건비 ═══ */}
      <div className="rounded-lg border border-[#262626] bg-[#161616] overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#262626]">
          <h3 className="text-xs font-medium text-[#ededed]">1. 직접인건비</h3>
          <button
            onClick={addLabor}
            className="text-[10px] text-[#3ecf8e] hover:text-[#3ecf8e]/80"
          >
            + 인력 추가
          </button>
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[#262626] text-[#8c8c8c]">
              <th className="py-2 px-2 text-left font-normal w-[15%]">등급</th>
              <th className="py-2 px-2 text-left font-normal w-[20%]">역할</th>
              <th className="py-2 px-2 text-right font-normal w-[20%]">
                월단가
              </th>
              <th className="py-2 px-2 text-center font-normal w-[10%]">MM</th>
              <th className="py-2 px-2 text-right font-normal w-[20%]">소계</th>
              <th className="py-2 px-1 w-[5%]"></th>
            </tr>
          </thead>
          <tbody>
            {labor.map((item, i) => (
              <LaborRow
                key={i}
                item={item}
                index={i}
                onChange={handleLaborChange}
                onRemove={removeLabor}
              />
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-[#333] bg-[#1a1a1a]">
              <td
                colSpan={3}
                className="py-2 px-2 text-xs font-medium text-[#ededed]"
              >
                합계
              </td>
              <td className="py-2 px-2 text-center text-xs font-mono text-[#ededed]">
                {totalMM.toFixed(1)}
              </td>
              <td className="py-2 px-2 text-right text-xs font-mono font-medium text-[#ededed]">
                {fmtWon(laborTotal)}
              </td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* ═══ 2. 직접경비 (그룹+세부항목) ═══ */}
      <div className="rounded-lg border border-[#262626] bg-[#161616] overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#262626]">
          <h3 className="text-xs font-medium text-[#ededed]">2. 직접경비</h3>
          <button
            onClick={addExpenseGroup}
            className="text-[10px] text-[#3ecf8e] hover:text-[#3ecf8e]/80"
          >
            + 항목 추가
          </button>
        </div>
        <div className="divide-y divide-[#1f1f1f]">
          {expenseGroups.map((group, gi) => {
            const groupTotal = group.subitems.reduce((s, e) => s + e.amount, 0);
            return (
              <div key={gi} className="px-4 py-2">
                {/* 그룹 헤더 */}
                <div className="flex items-center gap-2 mb-1.5">
                  <input
                    value={group.name}
                    onChange={(e) => updateGroupName(gi, e.target.value)}
                    className="flex-1 bg-transparent text-xs font-medium text-[#ededed] outline-none"
                    placeholder="항목 분류명"
                  />
                  <span className="text-xs font-mono text-[#8c8c8c]">
                    {fmtWon(groupTotal)}
                  </span>
                  <button
                    onClick={() => addSubitem(gi)}
                    className="text-[9px] text-blue-400/70 hover:text-blue-400"
                  >
                    +세부
                  </button>
                  <button
                    onClick={() => removeExpenseGroup(gi)}
                    className="text-[9px] text-red-400/30 hover:text-red-400"
                  >
                    ✕전체
                  </button>
                </div>
                {/* 세부항목 */}
                <div className="pl-4 space-y-1">
                  {group.subitems.map((sub, si) => (
                    <div key={si} className="flex items-center gap-2 group">
                      <span className="text-[#333] text-[10px]">├</span>
                      <input
                        value={sub.name}
                        onChange={(e) =>
                          updateSubitem(gi, si, "name", e.target.value)
                        }
                        placeholder="세부항목명"
                        className="w-[25%] bg-transparent text-xs text-[#ededed] outline-none"
                      />
                      <input
                        type="number"
                        value={sub.amount}
                        onChange={(e) =>
                          updateSubitem(
                            gi,
                            si,
                            "amount",
                            parseInt(e.target.value) || 0,
                          )
                        }
                        className="w-[25%] bg-transparent text-xs text-[#ededed] text-right outline-none font-mono"
                      />
                      <input
                        value={sub.basis}
                        onChange={(e) =>
                          updateSubitem(gi, si, "basis", e.target.value)
                        }
                        placeholder="산출근거"
                        className="flex-1 bg-transparent text-xs text-[#8c8c8c] outline-none"
                      />
                      <button
                        onClick={() => removeSubitem(gi, si)}
                        className="text-red-400/20 group-hover:text-red-400/60 hover:!text-red-400 text-[10px]"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        {/* 경비 합계 */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-[#333] bg-[#1a1a1a]">
          <span className="text-xs font-medium text-[#ededed]">합계</span>
          <span className="text-xs font-mono font-medium text-[#ededed]">
            {fmtWon(expenseTotal)}
          </span>
        </div>
      </div>

      {/* ═══ 3. 간접비·기술료 ═══ */}
      <div className="rounded-lg border border-[#262626] bg-[#161616] p-4">
        <h3 className="text-xs font-medium text-[#ededed] mb-3">
          3. 간접비 및 기술료
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-[10px] text-[#8c8c8c]">간접비율</label>
            <div className="flex items-center gap-2 mt-1">
              <input
                type="range"
                min="0"
                max="200"
                value={overheadRate}
                onChange={(e) => setOverheadRate(parseInt(e.target.value))}
                className="flex-1 h-1.5 rounded-full appearance-none cursor-pointer accent-purple-400"
              />
              <input
                type="number"
                min="0"
                max="200"
                value={overheadRate}
                onChange={(e) => setOverheadRate(parseInt(e.target.value) || 0)}
                className="w-14 px-1.5 py-1 bg-[#0a0a0a] border border-[#333] rounded text-xs text-[#ededed] text-right font-mono focus:border-[#3ecf8e] outline-none"
              />
              <span className="text-[10px] text-[#8c8c8c] w-2">%</span>
            </div>
            <p className="text-[10px] text-[#555] mt-1">
              직접인건비({fmtShort(laborTotal)}) × {overheadRate}% ={" "}
              {fmtShort(overheadTotal)}
            </p>
          </div>
          <div>
            <label className="text-[10px] text-[#8c8c8c]">기술료율</label>
            <div className="flex items-center gap-2 mt-1">
              <input
                type="range"
                min="0"
                max="50"
                value={profitRate}
                onChange={(e) => setProfitRate(parseInt(e.target.value))}
                className="flex-1 h-1.5 rounded-full appearance-none cursor-pointer accent-green-400"
              />
              <input
                type="number"
                min="0"
                max="50"
                value={profitRate}
                onChange={(e) => setProfitRate(parseInt(e.target.value) || 0)}
                className="w-14 px-1.5 py-1 bg-[#0a0a0a] border border-[#333] rounded text-xs text-[#ededed] text-right font-mono focus:border-[#3ecf8e] outline-none"
              />
              <span className="text-[10px] text-[#8c8c8c] w-2">%</span>
            </div>
            <p className="text-[10px] text-[#555] mt-1">
              (인건비+간접비)({fmtShort(laborTotal + overheadTotal)}) ×{" "}
              {profitRate}% = {fmtShort(profitTotal)}
            </p>
          </div>
        </div>
      </div>

      {/* ═══ 액션 ═══ */}
      <div className="flex items-center justify-between pt-2">
        <div>
          <p className="text-xs text-[#8c8c8c]">
            합계:{" "}
            <span className="text-[#3ecf8e] font-mono font-medium text-sm">
              {fmtWon(grandTotal)}
            </span>
            <span className="ml-2 text-[#555]">(VAT {fmtWon(vat)})</span>
          </p>
          <p className="text-[10px] text-[#555] mt-0.5">
            인건비 {actualRatios.labor}% · 경비 {actualRatios.expense}% · 간접비{" "}
            {actualRatios.overhead}% · 기술료 {actualRatios.profit}%
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating || labor.length === 0}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#3ecf8e] text-sm font-medium text-[#0a0a0a] hover:bg-[#3ecf8e]/90 transition-colors disabled:opacity-50"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          {generating ? "생성 중..." : "산출내역서 확정 및 다운로드"}
        </button>
      </div>
    </div>
  );
}
