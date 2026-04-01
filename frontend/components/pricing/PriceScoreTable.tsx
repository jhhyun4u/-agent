"use client";

/**
 * 가격점수 시뮬레이션 테이블
 *
 * 입찰가별 가격점수·예상총점을 테이블로 표시하여
 * 최적 입찰가 결정을 지원한다.
 */

import { useState } from "react";
import type { ScoreSimulationRow } from "@/lib/api";

interface Props {
  rows: ScoreSimulationRow[];
  recommendedRatio?: number;
}

function fmtWon(amount: number): string {
  if (Math.abs(amount) >= 100_000_000)
    return `${(amount / 100_000_000).toFixed(1)}억`;
  if (Math.abs(amount) >= 10_000) return `${(amount / 10_000).toFixed(0)}만`;
  return `${amount.toLocaleString()}`;
}

export default function PriceScoreTable({ rows, recommendedRatio }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (!rows || rows.length === 0) return null;

  // 최고 총점 행 찾기
  const validRows = rows.filter((r) => !r.is_disqualified);
  const maxScore =
    validRows.length > 0 ? Math.max(...validRows.map((r) => r.total_score)) : 0;

  const formula = rows[0]?.formula_used || "";
  const techScore = rows[0]?.tech_score ?? 0;
  const techWeight = rows[0]?.tech_weight ?? 0;
  const priceWeight = rows[0]?.price_weight ?? 0;
  const estMinBid = rows[0]?.estimated_min_bid ?? 0;

  // 축약 모드: 추천 비율 ±10% 범위만 표시
  const displayRows = expanded
    ? rows
    : rows.filter((r) => {
        if (!recommendedRatio) return true;
        return Math.abs(r.bid_ratio - recommendedRatio) <= 10;
      });

  return (
    <div className="rounded-lg border border-[#262626] bg-[#161616] p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-[#ededed]">
          가격점수 시뮬레이션
        </h3>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-[#8c8c8c] hover:text-[#ededed] transition-colors"
        >
          {expanded ? "축소" : "전체 보기"}
        </button>
      </div>

      {/* 가정 정보 */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#8c8c8c]">
        <span>
          기술점수:{" "}
          <span className="text-[#ededed]">
            {techScore}/{techWeight}점
          </span>{" "}
          (가정)
        </span>
        <span>
          가격배점: <span className="text-[#ededed]">{priceWeight}점</span>
        </span>
        <span>
          추정최저가:{" "}
          <span className="text-[#ededed]">{fmtWon(estMinBid)}원</span>
        </span>
      </div>

      {/* 공식 */}
      <div className="text-[10px] text-[#666] truncate" title={formula}>
        {formula}
      </div>

      {/* 테이블 */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[#333] text-[#8c8c8c]">
              <th className="py-2 pr-2 text-right font-normal">낙찰률</th>
              <th className="py-2 px-2 text-right font-normal">입찰가</th>
              <th className="py-2 px-2 text-right font-normal">가격점수</th>
              <th className="py-2 px-2 text-right font-normal">총점</th>
              <th className="py-2 pl-2 text-center font-normal">비고</th>
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row) => {
              const isRecommended =
                recommendedRatio &&
                Math.abs(row.bid_ratio - recommendedRatio) < 0.5;
              const isBest =
                !row.is_disqualified && row.total_score === maxScore;
              const isDisq = row.is_disqualified;

              return (
                <tr
                  key={row.bid_ratio}
                  className={`border-b border-[#1f1f1f] transition-colors ${
                    isDisq
                      ? "text-[#555] line-through"
                      : isRecommended
                        ? "bg-[#3ecf8e]/5"
                        : isBest
                          ? "bg-blue-500/5"
                          : "hover:bg-[#1a1a1a]"
                  }`}
                >
                  <td className="py-1.5 pr-2 text-right font-mono text-[#ededed]">
                    {row.bid_ratio.toFixed(1)}%
                  </td>
                  <td className="py-1.5 px-2 text-right text-[#ededed]">
                    {fmtWon(row.bid_price)}원
                  </td>
                  <td className="py-1.5 px-2 text-right font-mono">
                    <span className={isDisq ? "" : "text-[#ededed]"}>
                      {row.price_score.toFixed(2)}
                    </span>
                    <span className="text-[#555]">/{row.price_weight}</span>
                  </td>
                  <td
                    className={`py-1.5 px-2 text-right font-mono font-medium ${
                      isDisq ? "" : isBest ? "text-blue-400" : "text-[#ededed]"
                    }`}
                  >
                    {row.total_score.toFixed(2)}
                  </td>
                  <td className="py-1.5 pl-2 text-center">
                    {isDisq && (
                      <span className="text-[10px] text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded">
                        탈락
                      </span>
                    )}
                    {!isDisq && isRecommended && (
                      <span className="text-[10px] text-[#3ecf8e] bg-[#3ecf8e]/10 px-1.5 py-0.5 rounded">
                        추천
                      </span>
                    )}
                    {!isDisq && !isRecommended && isBest && (
                      <span className="text-[10px] text-blue-400 bg-blue-400/10 px-1.5 py-0.5 rounded">
                        최고점
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 인사이트 */}
      {validRows.length > 1 && (
        <div className="text-[11px] text-[#8c8c8c] space-y-0.5">
          {(() => {
            const bestRow = validRows.reduce((a, b) =>
              a.total_score > b.total_score ? a : b,
            );
            const recRow = validRows.find(
              (r) =>
                recommendedRatio &&
                Math.abs(r.bid_ratio - recommendedRatio) < 0.5,
            );
            if (recRow && bestRow.bid_ratio !== recRow.bid_ratio) {
              const scoreDiff = (
                bestRow.total_score - recRow.total_score
              ).toFixed(1);
              const priceDiff = fmtWon(
                Math.abs(bestRow.bid_price - recRow.bid_price),
              );
              return (
                <p>
                  총점 최대화: {bestRow.bid_ratio.toFixed(1)}% (
                  {fmtWon(bestRow.bid_price)}원) → 추천 대비{" "}
                  <span className="text-blue-400">+{scoreDiff}점</span>, 입찰가{" "}
                  <span className="text-[#ededed]">
                    {priceDiff}원{" "}
                    {bestRow.bid_price < recRow.bid_price ? "절감" : "추가"}
                  </span>
                </p>
              );
            }
            return null;
          })()}
        </div>
      )}
    </div>
  );
}
