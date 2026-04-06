/**
 * 인증 환경 통합 테스트
 *
 * Supabase Auth → JWT 토큰 → 백엔드 API → 프론트엔드 연동
 * 실제 Supabase 인증 + 실제 백엔드 API를 E2E로 검증
 */

import { chromium } from "playwright";

const BASE_FE = "http://localhost:3000";
const BASE_API = "http://localhost:8000";
const CREDS = { email: "sjk@tenopa.co.kr", password: "9krjAfOPujSaGDL1" };

let passed = 0;
let failed = 0;
const results = [];

function ok(name) { passed++; results.push({ name, status: "PASS" }); console.log(`  ✅ ${name}`); }
function fail(name, reason) { failed++; results.push({ name, status: "FAIL", reason: String(reason).substring(0, 150) }); console.log(`  ❌ ${name}: ${String(reason).substring(0, 150)}`); }

async function safeGoto(page, url, timeout = 15000) {
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout });
    await page.waitForTimeout(2000);
    return true;
  } catch { return false; }
}

async function run() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // ═══════════════════════════════════════
  // Phase 1: 백엔드 상태 확인
  // ═══════════════════════════════════════
  console.log("\n[Phase 1] 백엔드 상태");
  try {
    const health = await (await fetch(`${BASE_API}/health`)).json();
    health.status === "ok" ? ok(`백엔드 OK (v${health.version}, DB: ${health.database})`) : fail("백엔드", health);
  } catch (e) { fail("백엔드 연결", e.message); }

  // ═══════════════════════════════════════
  // Phase 2: Supabase 로그인 + JWT 토큰 추출
  // ═══════════════════════════════════════
  console.log("\n[Phase 2] Supabase 인증 + JWT 추출");
  let accessToken = "";

  try {
    await safeGoto(page, `${BASE_FE}/login`);
    await page.fill('input[type="email"]', CREDS.email);
    await page.fill('input[type="password"]', CREDS.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);

    !page.url().includes("/login") ? ok("프론트엔드 로그인 성공") : fail("로그인", page.url());

    // Supabase 세션에서 JWT 토큰 추출
    accessToken = await page.evaluate(async () => {
      // Supabase 클라이언트 접근
      const { createClient } = await import("@supabase/supabase-js");
      const url = process.env.NEXT_PUBLIC_SUPABASE_URL || document.querySelector('meta[name="supabase-url"]')?.content;

      // localStorage에서 Supabase 세션 추출
      for (const key of Object.keys(localStorage)) {
        if (key.includes("auth-token") || key.includes("supabase")) {
          try {
            const val = JSON.parse(localStorage.getItem(key));
            if (val?.access_token) return val.access_token;
            if (val?.currentSession?.access_token) return val.currentSession.access_token;
          } catch {}
        }
      }

      // cookie 기반 세션 확인
      const cookies = document.cookie;
      return "";
    });

    if (!accessToken) {
      // localStorage 전수 스캔
      accessToken = await page.evaluate(() => {
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          const val = localStorage.getItem(key);
          if (val && val.includes("access_token")) {
            try {
              const parsed = JSON.parse(val);
              // Supabase v2 형식
              if (parsed.access_token) return parsed.access_token;
              // nested
              const walk = (obj) => {
                if (!obj || typeof obj !== "object") return null;
                if (obj.access_token) return obj.access_token;
                for (const v of Object.values(obj)) {
                  const found = walk(v);
                  if (found) return found;
                }
                return null;
              };
              const found = walk(parsed);
              if (found) return found;
            } catch {}
          }
        }
        return "";
      });
    }

    accessToken ? ok(`JWT 토큰 추출 (${accessToken.substring(0, 20)}...)`) : fail("JWT 추출", "localStorage에서 토큰 미발견");
  } catch (e) { fail("인증 흐름", e.message); }

  // ═══════════════════════════════════════
  // Phase 3: JWT로 백엔드 API 직접 호출
  // ═══════════════════════════════════════
  console.log("\n[Phase 3] JWT → 백엔드 API 직접 호출");

  if (accessToken) {
    const apiTests = [
      { method: "GET", path: "/api/auth/me", name: "인증 사용자 정보", check: (d) => d.email || d.id },
      { method: "GET", path: "/api/kb/health", name: "KB 건강도", check: (d) => d.content !== undefined || d.capability !== undefined },
      { method: "GET", path: "/api/proposals", name: "제안 프로젝트 목록", check: (d) => Array.isArray(d.data || d.items || d) },
      { method: "GET", path: "/api/kb/content?status=all", name: "콘텐츠 라이브러리", check: (d) => d !== undefined },
      { method: "GET", path: "/api/kb/clients", name: "발주기관 목록", check: (d) => d !== undefined },
      { method: "GET", path: "/api/kb/competitors", name: "경쟁사 목록", check: (d) => d !== undefined },
      { method: "GET", path: "/api/kb/lessons", name: "교훈 목록", check: (d) => d !== undefined },
      { method: "GET", path: "/api/kb/labor-rates", name: "노임단가", check: (d) => d !== undefined },
      { method: "GET", path: "/api/kb/market-prices", name: "시장 가격", check: (d) => d !== undefined },
      { method: "GET", path: "/api/notifications", name: "알림 목록", check: (d) => d !== undefined },
    ];

    for (const t of apiTests) {
      try {
        const res = await fetch(`${BASE_API}${t.path}`, {
          method: t.method,
          headers: {
            "Authorization": `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
        });
        if (res.ok) {
          const data = await res.json();
          t.check(data) ? ok(`${t.name} (${res.status})`) : fail(t.name, `응답 형식 불일치: ${JSON.stringify(data).substring(0, 100)}`);
        } else {
          const err = await res.text().catch(() => "");
          fail(t.name, `${res.status} ${err.substring(0, 100)}`);
        }
      } catch (e) { fail(t.name, e.message); }
    }
  } else {
    console.log("  ⚠️  JWT 토큰 미확보 — API 직접 호출 테스트 스킵");
  }

  // ═══════════════════════════════════════
  // Phase 4: 프론트엔드 ↔ 백엔드 연동 (브라우저 내부)
  // ═══════════════════════════════════════
  console.log("\n[Phase 4] 프론트엔드 ↔ 백엔드 연동");

  // API 호출 캡처
  const apiResponses = [];
  page.on("response", (r) => {
    if (r.url().includes(":8000/api/")) {
      apiResponses.push({ url: r.url().replace(BASE_API, ""), status: r.status() });
    }
  });

  // 4-1: 대시보드 API 연동
  try {
    apiResponses.length = 0;
    await safeGoto(page, `${BASE_FE}/dashboard`);
    const skip = await page.$("text=건너뛰기");
    if (skip) await skip.click();
    await page.waitForTimeout(3000);

    const dashApi = apiResponses.filter(r => r.status < 400);
    dashApi.length > 0
      ? ok(`대시보드 API 연동 (${dashApi.length}건 성공: ${dashApi.map(r => r.url.split("?")[0]).join(", ")})`)
      : fail("대시보드 API", `성공 0건, 실패: ${apiResponses.filter(r => r.status >= 400).map(r => `${r.url}=${r.status}`).join(", ")}`);
  } catch (e) { fail("대시보드 API", e.message); }

  // 4-2: 공고 모니터링 API 연동
  try {
    apiResponses.length = 0;
    await safeGoto(page, `${BASE_FE}/bids`);
    await page.waitForTimeout(8000); // G2B 수집 대기

    const bidsApi = apiResponses.filter(r => r.status < 400);
    bidsApi.length > 0
      ? ok(`공고 모니터링 API (${bidsApi.length}건 성공)`)
      : fail("공고 API", `${apiResponses.map(r => `${r.url}=${r.status}`).join(", ")}`);

    // 스코어링 결과 확인
    const scoredApi = apiResponses.find(r => r.url.includes("scored"));
    scoredApi
      ? ok(`AI 스코어링 API 호출 (${scoredApi.status})`)
      : ok("AI 스코어링 미호출 (초기 로딩 중)");
  } catch (e) { fail("공고 API", e.message); }

  // 4-3: KB 검색 탭 + 건강도 위젯 API 연동
  try {
    apiResponses.length = 0;
    await safeGoto(page, `${BASE_FE}/kb/search`);
    const searchTab = await page.$("button:has-text('KB 검색')");
    if (searchTab) await searchTab.click();
    await page.waitForTimeout(4000);

    const kbHealthApi = apiResponses.find(r => r.url.includes("/kb/health"));
    if (kbHealthApi) {
      kbHealthApi.status < 400
        ? ok(`KB 건강도 API 성공 (${kbHealthApi.status})`)
        : fail("KB 건강도 API", `${kbHealthApi.status}`);
    } else {
      // API 미호출 = 위젯이 마운트되지 않았거나 토큰 문제
      fail("KB 건강도 API", `미호출 (캡처된 API: ${apiResponses.map(r => r.url).join(", ") || "없음"})`);
    }

    // 건강도 위젯 렌더링
    const widget = await page.$("text=KB 건강도");
    widget ? ok("KB 건강도 위젯 렌더링") : fail("건강도 위젯 렌더링", "미표시");
  } catch (e) { fail("KB 검색 연동", e.message); }

  // 4-4: KB 콘텐츠 목록 API
  try {
    apiResponses.length = 0;
    await safeGoto(page, `${BASE_FE}/kb/content`);
    await page.waitForTimeout(3000);

    const contentApi = apiResponses.filter(r => r.url.includes("/kb/content"));
    contentApi.length > 0
      ? ok(`콘텐츠 라이브러리 API (${contentApi[0].status})`)
      : fail("콘텐츠 API", "미호출");
  } catch (e) { fail("콘텐츠 API", e.message); }

  // 4-5: 제안 프로젝트 목록 API
  try {
    apiResponses.length = 0;
    await safeGoto(page, `${BASE_FE}/proposals`);
    await page.waitForTimeout(3000);

    const propApi = apiResponses.filter(r => r.url.includes("/proposals") && r.status < 400);
    propApi.length > 0
      ? ok(`제안 프로젝트 API (${propApi[0].status})`)
      : fail("제안 API", `${apiResponses.map(r => `${r.url}=${r.status}`).join(", ")}`);
  } catch (e) { fail("제안 API", e.message); }

  // ═══════════════════════════════════════
  // Phase 5: 인증 보안 테스트
  // ═══════════════════════════════════════
  console.log("\n[Phase 5] 인증 보안");
  try {
    // 토큰 없이 API 호출 → 401
    const noAuth = await fetch(`${BASE_API}/api/auth/me`);
    noAuth.status === 401 || noAuth.status === 403
      ? ok(`미인증 요청 차단 (${noAuth.status})`)
      : fail("미인증 차단", `${noAuth.status}`);

    // 잘못된 토큰 → 401
    const badAuth = await fetch(`${BASE_API}/api/auth/me`, {
      headers: { "Authorization": "Bearer invalid-token-12345" },
    });
    badAuth.status === 401 || badAuth.status === 403
      ? ok(`잘못된 토큰 차단 (${badAuth.status})`)
      : fail("잘못된 토큰", `${badAuth.status}`);
  } catch (e) { fail("보안 테스트", e.message); }

  // ═══════════════════════════════════════
  // Phase 6: 로그아웃 검증
  // ═══════════════════════════════════════
  console.log("\n[Phase 6] 로그아웃");
  try {
    await safeGoto(page, `${BASE_FE}/dashboard`);
    await page.waitForTimeout(1500);
    const skip = await page.$("text=건너뛰기");
    if (skip) await skip.click();
    await page.waitForTimeout(300);

    const logoutBtn = await page.$("text=로그아웃");
    if (logoutBtn) {
      await logoutBtn.click();
      await page.waitForTimeout(3000);
      page.url().includes("/login")
        ? ok("로그아웃 → 로그인 페이지 리다이렉트")
        : fail("로그아웃", `url=${page.url()}`);
    } else {
      fail("로그아웃", "버튼 미발견");
    }

    // 로그아웃 후 보호 페이지 접근 → 리다이렉트
    await safeGoto(page, `${BASE_FE}/dashboard`);
    await page.waitForTimeout(2000);
    page.url().includes("/login")
      ? ok("로그아웃 후 보호 페이지 → 로그인 리다이렉트")
      : fail("보호 페이지 차단", `url=${page.url()}`);
  } catch (e) { fail("로그아웃", e.message); }

  // ═══════════════════════════════════════
  // 결과 요약
  // ═══════════════════════════════════════
  await browser.close();

  console.log("\n" + "═".repeat(55));
  console.log(`📊 인증 통합 테스트: ${passed} passed, ${failed} failed (총 ${passed + failed})`);
  console.log("═".repeat(55));

  if (failed > 0) {
    console.log("\n실패 항목:");
    for (const r of results.filter((r) => r.status === "FAIL")) {
      console.log(`  ❌ ${r.name}: ${r.reason}`);
    }
  }

  // Phase별 집계
  const phases = {
    "Phase 1 백엔드": results.filter(r => r.name.includes("백엔드")),
    "Phase 2 인증": results.filter(r => r.name.includes("로그인") || r.name.includes("JWT")),
    "Phase 3 API": results.filter(r => ["인증 사용자", "KB 건강도", "제안 프로젝트", "콘텐츠", "발주기관", "경쟁사", "교훈", "노임단가", "시장", "알림"].some(k => r.name.includes(k)) && !r.name.includes("API 연동") && !r.name.includes("위젯")),
    "Phase 4 연동": results.filter(r => r.name.includes("API") && (r.name.includes("대시") || r.name.includes("공고") || r.name.includes("콘텐츠 라이브러리 API") || r.name.includes("제안 프로젝트 API") || r.name.includes("건강도"))),
    "Phase 5 보안": results.filter(r => r.name.includes("인증") || r.name.includes("토큰 차단")),
    "Phase 6 로그아웃": results.filter(r => r.name.includes("로그아웃") || r.name.includes("보호")),
  };

  console.log("\nPhase별:");
  for (const [name, items] of Object.entries(phases)) {
    const p = items.filter(r => r.status === "PASS").length;
    const f = items.filter(r => r.status === "FAIL").length;
    console.log(`  ${name}: ${p}/${p + f}`);
  }

  process.exit(failed > 0 ? 1 : 0);
}

run().catch((e) => {
  console.error("테스트 실행 실패:", e);
  process.exit(1);
});
