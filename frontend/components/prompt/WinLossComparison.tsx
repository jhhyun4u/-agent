"use client";

/**
 * WinLossComparison — 수주/패찰 제안서 비교 테이블
 */

interface WinLossData {
  win_avg_quality: number;
  loss_avg_quality: number;
  win_count: number;
  loss_count: number;
  key_differences: string[];
}

interface WinLossComparisonProps {
  data: WinLossData;
}

export default function WinLossComparison({ data }: WinLossComparisonProps) {
  if (!data.win_count && !data.loss_count) {
    return <div className="text-xs text-[#8c8c8c]">수주/패찰 비교 데이터 없음</div>;
  }

  const diff = data.win_avg_quality - data.loss_avg_quality;

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold">수주 vs 패찰 비교</h3>
      <div className="grid grid-cols-3 gap-3 text-center text-xs">
        <div className="bg-[#1a3a2a] rounded-lg p-3 border border-[#2a4a3a]">
          <div className="text-[#8c8c8c]">수주 제안서</div>
          <div className="text-lg font-bold text-[#3ecf8e]">{data.win_avg_quality}점</div>
          <div className="text-[#8c8c8c]">{data.win_count}건</div>
        </div>
        <div className="bg-[#2a1a1a] rounded-lg p-3 border border-[#4a2020]">
          <div className="text-[#8c8c8c]">패찰 제안서</div>
          <div className="text-lg font-bold text-[#ff6b6b]">{data.loss_avg_quality}점</div>
          <div className="text-[#8c8c8c]">{data.loss_count}건</div>
        </div>
        <div className="bg-[#111] rounded-lg p-3 border border-[#262626]">
          <div className="text-[#8c8c8c]">차이</div>
          <div className={`text-lg font-bold ${diff > 0 ? "text-[#3ecf8e]" : "text-[#ff6b6b]"}`}>
            {diff > 0 ? "+" : ""}{diff.toFixed(1)}점
          </div>
        </div>
      </div>
      {data.key_differences.length > 0 && (
        <div className="text-xs text-[#8c8c8c] space-y-1">
          {data.key_differences.map((d, i) => (
            <div key={i}>→ {d}</div>
          ))}
        </div>
      )}
    </div>
  );
}
