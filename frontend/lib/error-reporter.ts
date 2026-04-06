/**
 * 프론트엔드 글로벌 에러 리포터 (MON-10)
 *
 * window.onerror + unhandledrejection 캡처 → POST /api/client-errors
 */

const ERROR_ENDPOINT = "/api/client-errors";
let recentErrors: string[] = [];

export function initErrorReporter() {
  if (typeof window === "undefined") return;

  window.addEventListener("error", (event) => {
    reportError({
      url: window.location.href,
      error: event.message,
      stack: event.error?.stack,
    });
  });

  window.addEventListener("unhandledrejection", (event) => {
    reportError({
      url: window.location.href,
      error: String(event.reason),
      stack: event.reason?.stack,
    });
  });
}

async function reportError(payload: {
  url: string;
  error: string;
  stack?: string;
  metadata?: Record<string, unknown>;
}) {
  // 동일 에러 1분 내 중복 방지
  const key = `${payload.error}:${payload.url}`;
  if (recentErrors.includes(key)) return;
  recentErrors.push(key);
  setTimeout(() => {
    recentErrors = recentErrors.filter((e) => e !== key);
  }, 60_000);

  try {
    await fetch(ERROR_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    // 에러 리포터 자체 실패는 무시
  }
}
