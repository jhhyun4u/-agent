/**
 * 타이포그래피 시스템 — 모든 텍스트 스타일 상수
 *
 * 사용법:
 * import { TEXT_SIZES } from "@/lib/typography";
 *
 * <h1 className={TEXT_SIZES.h1}>제목</h1>
 * <p className={TEXT_SIZES.body}>본문</p>
 */

export const TEXT_SIZES = {
  // 제목
  h1: "text-3xl font-bold tracking-tight leading-tight",
  h2: "text-2xl font-semibold tracking-tight leading-snug",
  h3: "text-xl font-semibold tracking-tight leading-snug",
  h4: "text-lg font-semibold tracking-normal",

  // 본문
  body: "text-sm leading-6 text-[#ededed]",
  bodyLarge: "text-base leading-7 text-[#ededed]",
  bodySmall: "text-xs leading-5 text-[#ededed]",

  // 라벨/강조
  label: "text-sm font-medium text-[#ededed]",
  labelSmall: "text-xs font-medium uppercase tracking-wider text-[#8c8c8c]",

  // 보조 텍스트
  caption: "text-xs leading-4 text-[#8c8c8c]",
  muted: "text-xs leading-4 text-[#6b7280]",
  hint: "text-xs leading-4 text-[#8c8c8c] italic",

  // 특수
  code: "text-xs font-mono bg-[#111111] px-2 py-1 rounded text-[#3ecf8e]",
  error: "text-sm text-red-400 font-medium",
  success: "text-sm text-green-400 font-medium",
  warning: "text-sm text-yellow-400 font-medium",
  info: "text-sm text-blue-400 font-medium",
} as const;

/** 라이트 모드 텍스트 색상 (다크 모드는 CSS 변수 사용) */
export const TEXT_COLORS = {
  primary: "text-[#ededed]",
  secondary: "text-[#8c8c8c]",
  muted: "text-[#6b7280]",
  accent: "text-[#3ecf8e]",
  error: "text-red-400",
  success: "text-green-400",
  warning: "text-yellow-400",
  info: "text-blue-400",
} as const;

/** 빠른 조합 — 자주 사용되는 조합 */
export const TEXT_PRESETS = {
  pageTitle: `${TEXT_SIZES.h1} text-[#ededed]`,
  sectionTitle: `${TEXT_SIZES.h2} text-[#ededed]`,
  subsectionTitle: `${TEXT_SIZES.h3} text-[#ededed]`,
  cardTitle: `${TEXT_SIZES.h4} text-[#ededed]`,
  paragraph: `${TEXT_SIZES.body} text-[#ededed]`,
  description: `${TEXT_SIZES.bodySmall} text-[#8c8c8c]`,
  button: `${TEXT_SIZES.label} text-center`,
  badge: `${TEXT_SIZES.labelSmall} text-[#8c8c8c]`,
} as const;
