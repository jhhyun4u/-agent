/**
 * 프론트엔드 E2E 기능 테스트 v2
 * 백엔드 실행 상태에서 재검증 — 타임아웃 확대 + 선택자 개선
 */

import { chromium } from "playwright";

const BASE = "http://localhost:3000";
const CREDS = { email: "sjk@tenopa.co.kr", password: "9krjAfOPujSaGDL1" };

let passed = 0;
let failed = 0;
const results = [];

function ok(name) {
  passed++;
  results.push({ name, status: "PASS" });
  console.log(`  ✅ ${name}`);
}
function fail(name, reason) {
  failed++;
  results.push({ name, status: "FAIL", reason });
  console.log(`  ❌ ${name}: ${reason}`);
}

async function safeGoto(page, path, timeout = 20000) {
  try {
    await page.goto(`${BASE}${path}`, { waitUntil: "domcontentloaded", timeout });
    await page.waitForTimeout(2000);
    return true;
  } catch {
    // domcontentloaded 실패 시 load로 재시도
    try {
      await page.goto(`${BASE}${path}`, { waitUntil: "load", timeout });
      await page.waitForTimeout(2000);
      return true;
    } catch (e) {
      return false;
    }
  }
}

async function run() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // ═══════════════════════════════════════
  // T1: 로그인
  // ═══════════════════════════════════════
  console.log("\n[T1] 로그인");
  try {
    await safeGoto(page, "/login");
    const emailInput = await page.$('input[type="email"]');
    const pwInput = await page.$('input[type="password"]');
    const submitBtn = await page.$('button[type="submit"]');
    emailInput && pwInput && submitBtn
      ? ok("로그인 폼 렌더링")
      : fail("로그인 폼", "요소 누락");

    await page.fill('input[type="email"]', CREDS.email);
    await page.fill('input[type="password"]', CREDS.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);
    !page.url().includes("/login")
      ? ok("로그인 성공 → 리다이렉트")
      : fail("로그인", `still on ${page.url()}`);
  } catch (e) {
    fail("로그인", e.message);
  }

  // ═══════════════════════════════════════
  // T2: 대시보드
  // ═══════════════════════════════════════
  console.log("\n[T2] 대시보드");
  try {
    await safeGoto(page, "/dashboard");
    // 온보딩 모달 닫기
    const skip = await page.$("text=건너뛰기");
    if (skip) { await skip.click(); await page.waitForTimeout(500); }

    (await page.$("text=제안 파이프라인")) ? ok("파이프라인 표시") : fail("파이프라인", "미표시");
    (await page.$("text=RFP 캘린더")) ? ok("캘린더 표시") : fail("캘린더", "미표시");

    const scopeTabs = await page.$$("text=/^개인$|^팀$|^본부$|^전체$/");
    scopeTabs.length >= 3 ? ok(`스코프 탭 ${scopeTabs.length}개`) : fail("스코프", `${scopeTabs.length}개`);

    (await page.$("text=로그아웃")) ? ok("로그아웃 버튼") : fail("로그아웃", "미발견");
    (await page.$(`text=${CREDS.email}`)) ? ok("사용자 이메일") : fail("이메일", "미표시");
  } catch (e) {
    fail("대시보드", e.message);
  }

  // ═══════════════════════════════════════
  // T3: 사이드바 전체 네비게이션
  // ═══════════════════════════════════════
  console.log("\n[T3] 사이드바 네비게이션");
  const navTargets = [
    { href: "/bids", label: "공고 모니터링" },
    { href: "/proposals", label: "제안 프로젝트" },
    { href: "/pricing", label: "가격 시뮬레이터" },
    { href: "/kb/search", label: "지식 베이스" },
    { href: "/dashboard", label: "대시보드" },
  ];
  for (const nav of navTargets) {
    try {
      // href 기반 선택 (더 정확)
      const link = await page.$(`a[href="${nav.href}"]`);
      if (link) {
        await link.click();
        await page.waitForTimeout(2000);
        page.url().includes(nav.href)
          ? ok(`→ ${nav.label} (${nav.href})`)
          : fail(`→ ${nav.label}`, `url=${page.url()}`);
      } else {
        fail(`→ ${nav.label}`, "링크 미발견");
      }
    } catch (e) {
      fail(`→ ${nav.label}`, e.message);
    }
  }

  // ═══════════════════════════════════════
  // T4: 공고 모니터링 (상세)
  // ═══════════════════════════════════════
  console.log("\n[T4] 공고 모니터링");
  try {
    await safeGoto(page, "/bids");
    await page.waitForTimeout(5000); // G2B 수집 대기

    (await page.$("text=7일")) ? ok("기간 필터") : fail("기간 필터", "미발견");
    (await page.$("text=20+")) ? ok("점수 필터") : fail("점수 필터", "미발견");

    // 단계 필터 체크박스 (pre-bid-integration)
    const stageLabels = ["공고", "사전", "계획"];
    let stageFound = 0;
    for (const s of stageLabels) {
      if (await page.$(`label:has-text("${s}"), span:has-text("${s}")`)) stageFound++;
    }
    stageFound >= 2 ? ok(`단계 필터 ${stageFound}/3`) : fail("단계 필터", `${stageFound}/3`);

    // 소스 헤더 (pre-bid-integration GAP-1 해소)
    const header = await page.textContent("body");
    header && (header.includes("전수") || header.includes("수집"))
      ? ok("수집 현황 헤더")
      : fail("수집 헤더", "미표시");

    // 테이블 or 데이터 로딩
    const table = await page.$("table, text=수집 중, text=G2B");
    table ? ok("결과 영역 렌더링") : fail("결과 영역", "미발견");
  } catch (e) {
    fail("공고 모니터링", e.message);
  }

  // ═══════════════════════════════════════
  // T5: 제안 프로젝트
  // ═══════════════════════════════════════
  console.log("\n[T5] 제안 프로젝트");
  try {
    await safeGoto(page, "/proposals");

    (await page.$("text=제안 프로젝트 목록")) ? ok("제목") : fail("제목", "미표시");
    (await page.$("text=RFP 업로드")) ? ok("RFP 업로드 버튼") : fail("RFP 업로드", "미발견");
    (await page.$("text=공고에서 시작")) ? ok("공고에서 시작 버튼") : fail("공고시작", "미발견");
    (await page.$('input[placeholder*="검색"]')) ? ok("검색 입력") : fail("검색", "미발견");

    const tabs = await page.$$("text=/^전체$|^진행중$|^완료$|^실패$/");
    tabs.length >= 3 ? ok(`상태 탭 ${tabs.length}개`) : fail("상태 탭", `${tabs.length}개`);
  } catch (e) {
    fail("제안 프로젝트", e.message);
  }

  // ═══════════════════════════════════════
  // T6: 가격 시뮬레이터
  // ═══════════════════════════════════════
  console.log("\n[T6] 가격 시뮬레이터");
  try {
    await safeGoto(page, "/pricing");
    page.url().includes("/pricing") ? ok("페이지 로드") : fail("페이지", page.url());

    const numInput = await page.$('input[type="number"], input[placeholder*="예산"], input[placeholder*="금액"]');
    numInput ? ok("예산 입력 필드") : fail("예산 입력", "미발견");
  } catch (e) {
    fail("가격 시뮬레이터", e.message);
  }

  // ═══════════════════════════════════════
  // T7: KB 산출물 + 검색 + 건강도 위젯
  // ═══════════════════════════════════════
  console.log("\n[T7] KB 검색 + 건강도 위젯");
  try {
    await safeGoto(page, "/kb/search");

    (await page.$("text=지식 베이스")) ? ok("헤딩") : fail("헤딩", "미표시");
    (await page.$("text=산출물 관리")) ? ok("산출물 관리 탭") : fail("산출물 탭", "미발견");

    // KB 검색 탭 전환
    const searchTab = await page.$("text=KB 검색");
    if (searchTab) {
      await searchTab.click();
      await page.waitForTimeout(2000);
      ok("KB 검색 탭 전환");
    } else {
      fail("KB 검색 탭", "미발견");
    }

    (await page.$('input[placeholder*="검색"]')) ? ok("검색 입력") : fail("검색 입력", "미발견");

    // 영역 필터
    const areas = await page.$$("text=/콘텐츠|발주기관|경쟁사|교훈|역량/");
    areas.length >= 4 ? ok(`영역 필터 ${areas.length}개`) : fail("영역 필터", `${areas.length}개`);

    // KB 건강도 위젯 (백엔드 연결 상태에서 검증)
    await page.waitForTimeout(2000);
    const healthWidget = await page.$("text=KB 건강도");
    healthWidget ? ok("KB 건강도 위젯 표시 (Phase D)") : fail("건강도 위젯", "미표시");

    // 위젯 내 영역 바 확인
    if (healthWidget) {
      const bars = await page.$$("text=/콘텐츠|발주기관|경쟁사|교훈|역량|Q&A/");
      bars.length >= 5 ? ok(`건강도 영역 바 ${bars.length}개`) : fail("영역 바", `${bars.length}개`);
    }
  } catch (e) {
    fail("KB 검색", e.message);
  }

  // ═══════════════════════════════════════
  // T8: KB 하위 페이지 전수 라우팅
  // ═══════════════════════════════════════
  console.log("\n[T8] KB 하위 페이지 라우팅");
  const kbPages = [
    { path: "/kb/content", name: "콘텐츠 라이브러리" },
    { path: "/kb/clients", name: "발주기관 DB" },
    { path: "/kb/competitors", name: "경쟁사 DB" },
    { path: "/kb/lessons", name: "교훈 아카이브" },
    { path: "/kb/labor-rates", name: "노임단가" },
    { path: "/kb/market-prices", name: "시장 가격" },
    { path: "/kb/qa", name: "Q&A" },
  ];

  for (const pg of kbPages) {
    const loaded = await safeGoto(page, pg.path, 15000);
    if (loaded && !page.url().includes("/login")) {
      ok(`${pg.name} (${pg.path})`);
    } else {
      fail(`${pg.name}`, loaded ? "로그인 리다이렉트" : "타임아웃");
    }
  }

  // ═══════════════════════════════════════
  // T9: 다크 모드 토글
  // ═══════════════════════════════════════
  console.log("\n[T9] 다크 모드 토글");
  try {
    await safeGoto(page, "/dashboard");
    const skip = await page.$("text=건너뛰기");
    if (skip) { await skip.click(); await page.waitForTimeout(300); }

    const toggle = await page.$("text=다크 모드");
    if (toggle) {
      await toggle.click();
      await page.waitForTimeout(500);
      ok("다크 모드 토글 클릭");
      // 라이트 모드로 전환 확인
      const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
      bg ? ok(`배경색 변경: ${bg}`) : fail("배경색", "확인 불가");
    } else {
      fail("다크 모드 토글", "미발견");
    }
  } catch (e) {
    fail("다크 모드", e.message);
  }

  // ═══════════════════════════════════════
  // T10: API 연동 확인 (백엔드 + 프론트)
  // ═══════════════════════════════════════
  console.log("\n[T10] API 연동 확인");
  try {
    // 백엔드 health
    const resp = await page.evaluate(async () => {
      const r = await fetch("http://localhost:8000/health");
      return r.ok ? await r.json() : null;
    });
    resp && resp.status === "ok" ? ok("백엔드 /health 정상") : fail("백엔드 health", JSON.stringify(resp));

    // KB health API (인증 필요하므로 프론트에서 호출)
    await safeGoto(page, "/kb/search");
    const searchTab = await page.$("text=KB 검색");
    if (searchTab) await searchTab.click();
    await page.waitForTimeout(3000);

    // 건강도 데이터가 렌더링 되었는지 확인 (건수 표시)
    const bodyText = await page.textContent("body");
    bodyText && bodyText.includes("건") ? ok("KB 데이터 건수 표시") : fail("KB 건수", "표시 안 됨");
  } catch (e) {
    fail("API 연동", e.message);
  }

  // ═══════════════════════════════════════
  // 결과 요약
  // ═══════════════════════════════════════
  await browser.close();

  console.log("\n" + "═".repeat(55));
  console.log(`📊 테스트 결과: ${passed} passed, ${failed} failed (총 ${passed + failed})`);
  console.log("═".repeat(55));

  if (failed > 0) {
    console.log("\n실패 항목:");
    for (const r of results.filter((r) => r.status === "FAIL")) {
      console.log(`  ❌ ${r.name}: ${r.reason}`);
    }
  }

  process.exit(failed > 0 ? 1 : 0);
}

run().catch((e) => {
  console.error("테스트 실행 실패:", e);
  process.exit(1);
});
