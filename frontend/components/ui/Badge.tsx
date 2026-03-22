/**
 * Badge — 공통 상태 배지 컴포넌트
 */

interface BadgeProps {
  children: React.ReactNode;
  variant?: "success" | "warning" | "error" | "info" | "neutral";
  size?: "xs" | "sm";
}

const VARIANTS = {
  success: "bg-[#3ecf8e]/15 text-[#3ecf8e]",
  warning: "bg-amber-500/15 text-amber-400",
  error: "bg-red-500/15 text-red-400",
  info: "bg-blue-500/15 text-blue-400",
  neutral: "bg-[#262626] text-[#8c8c8c]",
} as const;

const SIZES = {
  xs: "px-1.5 py-0.5 text-[9px]",
  sm: "px-2 py-0.5 text-[10px]",
} as const;

export default function Badge({ children, variant = "neutral", size = "sm" }: BadgeProps) {
  return (
    <span className={`inline-flex items-center font-medium rounded ${VARIANTS[variant]} ${SIZES[size]}`}>
      {children}
    </span>
  );
}
