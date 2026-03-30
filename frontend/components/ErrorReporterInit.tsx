"use client";

import { useEffect } from "react";
import { initErrorReporter } from "@/lib/error-reporter";

/** 글로벌 에러 리포터 초기화 (MON-10) */
export default function ErrorReporterInit() {
  useEffect(() => {
    initErrorReporter();
  }, []);
  return null;
}
