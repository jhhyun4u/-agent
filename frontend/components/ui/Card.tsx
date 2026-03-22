/**
 * Card — 공통 카드 컴포넌트
 */

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "bordered" | "elevated";
}

const VARIANTS = {
  default: "bg-[var(--card)] rounded-xl",
  bordered: "bg-[var(--card)] border border-[var(--border)] rounded-xl",
  elevated: "bg-[var(--card)] border border-[var(--border)] rounded-2xl shadow-lg",
} as const;

export default function Card({ children, className = "", variant = "bordered" }: CardProps) {
  return (
    <div className={`${VARIANTS[variant]} ${className}`}>
      {children}
    </div>
  );
}
