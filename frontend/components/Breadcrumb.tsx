"use client";

/**
 * Breadcrumb — 경로 기반 브레드크럼 네비게이션
 */

import { Fragment } from "react";
import Link from "next/link";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="flex items-center gap-1 text-[10px]" aria-label="breadcrumb">
      {items.map((item, i) => (
        <Fragment key={i}>
          {i > 0 && <span className="text-[#5c5c5c]">/</span>}
          {item.href ? (
            <Link
              href={item.href}
              className="text-[#8c8c8c] hover:text-[#ededed] transition-colors"
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-[#ededed] font-medium">{item.label}</span>
          )}
        </Fragment>
      ))}
    </nav>
  );
}
