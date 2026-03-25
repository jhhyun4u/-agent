/**
 * 프론트엔드 E2E 기능 테스트
 * Playwright 기반 — 로그인 후 주요 페이지 기능 검증
 *
 * 실행: cd frontend && node ../tests/e2e_frontend.mjs
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

async function run() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // ═══════════════════════════════════════
  // T1: 로그인 페이지 렌더링
  // ═══════════════════════════════════════
  console.log("\n[T1] 로그인 페이지");
  try {
    await page.goto(`${BASE}/login`, { waitUntil: "networkidle", timeout: 15000 });
    const emailInput = await page.$('input[type="email"]');
    const pwInput = await page.$('input[type="password"]');
    const submitBtn = await page.$('button[type="submit"]');
    emailInput && pwInput && submitBtn
      ? ok("로그인 폼 렌더링 (이메일+비밀번호+버튼)")
      : fail("로그인 폼 렌더링", "input 또는 button 누락");

    const title = await page.textContent("h2, h1");
    title && title.includes("로그인")
      ? ok("로그인 제목 표시")
      : fail("로그인 제목", `expected '로그인', got '${title}'`);
  } catch (e) {
    fail("로그인 페이지 로드", e.message);
  }

  // ═══════════════════════════════════════
  // T2: 로그인 실행
  // ═══════════════════════════════════════
  console.log("\n[T2] 로그인 실행");
  try {
    await page.fill('input[type="email"]', CREDS.email);
    await page.fill('input[type="password"]', CREDS.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    const url = page.url();
    !url.includes("/login")
      ? ok("로그인 성공 (리다이렉트)")
      : fail("로그인 성공", `still on ${url}`);
  } catch (e) {
    fail("로그인 실행", e.message);
  }

  // ═══════════════════════════════════════
  // T3: 대시보드
  // ═══════════════════════════════════════
  console.log("\n[T3] 대시보드");
  try {
    await page.goto(`${BASE}/dashboard`, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForTimeout(2000);

    // 온보딩 모달 닫기
    const skipBtn = await page.$("text=건너뛰기");
    if (skipBtn) await skipBtn.click();
    await page.waitForTimeout(500);

    const pipeline = await page.$("text=제안 파이프라인");
    pipeline ? ok("제안 파이프라인 섹션 표시") : fail("파이프라인", "미표시");

    const calendar = await page.$("text=RFP 캘린더");
    calendar ? ok("RFP 캘린더 섹션 표시") : fail("캘린더", "미표시");

    // 스코프 탭 (개인/팀/본부/전체)
    const scopeTabs = await page.$$("text=/개인|팀|본부|전체/");
    scopeTabs.length >= 3
      ? ok(`스코프 탭 ${scopeTabs.length}개 표시`)
      : fail("스코프 탭", `${scopeTabs.length}개만 표시`);
  } catch (e) {
    fail("대시보드 로드", e.message);
  }

  // ═══════════════════════════════════════
  // T4: 사이드바 네비게이션
  // ═══════════════════════════════════════
  console.log("\n[T4] 사이드바 네비게이션");
  try {
    const navItems = [
      { text: "대시보드", path: "/dashboard" },
      { text: "공고 모니터링", path: "/bids" },
      { text: "제안 프로젝트", path: "/proposals" },
      { text: "가격 시뮬레이터", path: "/pricing" },
      { text: "지식 베이스", path: "/kb" },
    ];

    for (const nav of navItems) {
      const link = await page.$(`a:has-text("${nav.text}"), button:has-text("${nav.text}")`);
      if (link) {
        await link.click();
        await page.waitForTimeout(1500);
        const url = page.url();
        url.includes(nav.path)
          ? ok(`사이드바 → ${nav.text} (${nav.path})`)
          : fail(`사이드바 → ${nav.text}`, `url=${url}`);
      } else {
        fail(`사이드바 → ${nav.text}`, "링크 미발견");
      }
    }
  } catch (e) {
    fail("사이드바 네비게이션", e.message);
  }

  // ═══════════════════════════════════════
  // T5: 공고 모니터링
  // ═══════════════════════════════════════
  console.log("\n[T5] 공고 모니터링");
  try {
    await page.goto(`${BASE}/bids`, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForTimeout(3000);

    // 필터 컨트롤 존재
    const periodSelect = await page.$("text=7일");
    periodSelect ? ok("기간 필터 존재") : fail("기간 필터", "미발견");

    const scoreSelect = await page.$("text=20+");
    scoreSelect ? ok("점수 필터 존재") : fail("점수 필터", "미발견");

    // 단계 필터 (pre-bid-integration: 공고/사전/계획)
    const stageFilters = await page.$$("text=/공고|사전|계획/");
    stageFilters.length >= 2
      ? ok(`단계 필터 체크박스 ${stageFilters.length}개`)
      : fail("단계 필터", `${stageFilters.length}개`);

    // 프리셋 버튼
    const presetBtns = await page.$$("text=/1억|전략|D-7/");
    presetBtns.length >= 1
      ? ok(`프리셋 버튼 ${presetBtns.length}개`)
      : fail("프리셋 버튼", "미발견");
  } catch (e) {
    fail("공고 모니터링", e.message);
  }

  // ═══════════════════════════════════════
  // T6: 제안 프로젝트 목록
  // ═══════════════════════════════════════
  console.log("\n[T6] 제안 프로젝트 목록");
  try {
    await page.goto(`${BASE}/proposals`, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForTimeout(2000);

    const heading = await page.$("text=제안 프로젝트 목록");
    heading ? ok("제안 프로젝트 목록 제목") : fail("제목", "미표시");

    // 상태 필터 탭
    const statusTabs = await page.$$("text=/전체|진행중|완료|실패/");
    statusTabs.length >= 3
      ? ok(`상태 탭 ${statusTabs.length}개`)
      : fail("상태 탭", `${statusTabs.length}개`);

    // 진입 경로 버튼
    const rfpUpload = await page.$("text=RFP 업로드");
    rfpUpload ? ok("RFP 업로드 버튼 존재") : fail("RFP 업로드", "미발견");

    const fromBid = await page.$("text=공고에서 시작");
    fromBid ? ok("공고에서 시작 버튼 존재") : fail("공고에서 시작", "미발견");

    // 검색 입력
    const searchInput = await page.$('input[placeholder*="검색"]');
    searchInput ? ok("프로젝트 검색 입력 존재") : fail("검색 입력", "미발견");
  } catch (e) {
    fail("제안 프로젝트", e.message);
  }

  // ═══════════════════════════════════════
  // T7: 가격 시뮬레이터
  // ═══════════════════════════════════════
  console.log("\n[T7] 가격 시뮬레이터");
  try {
    await page.goto(`${BASE}/pricing`, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForTimeout(2000);

    const url = page.url();
    url.includes("/pricing")
      ? ok("가격 시뮬레이터 페이지 로드")
      : fail("페이지 로드", `url=${url}`);

    // 예산 입력 또는 시뮬레이션 관련 요소
    const budgetInput = await page.$('input[placeholder*="예산"], input[placeholder*="금액"], input[type="number"]');
    budgetInput
      ? ok("예산 입력 필드 존재")
      : fail("예산 입력", "미발견 (페이지 구조 확인 필요)");
  } catch (e) {
    fail("가격 시뮬레이터", e.message);
  }

  // ═══════════════════════════════════════
  // T8: KB — 산출물 관리 탭
  // ═══════════════════════════════════════
  console.log("\n[T8] KB 산출물 관리");
  try {
    await page.goto(`${BASE}/kb/search`, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForTimeout(2000);

    const heading = await page.$("text=지식 베이스");
    heading ? ok("지식 베이스 헤딩") : fail("헤딩", "미표시");

    // 탭 전환
    const artifactTab = await page.$("text=산출물 관리");
    const searchTab = await page.$("text=KB 검색");
    artifactTab && searchTab
      ? ok("산출물 관리 + KB 검색 탭 존재")
      : fail("탭", "누락");

    // 스코프+결과 필터
    const filters = await page.$$("text=/전체|팀|개인|수주|패찰|미정/");
    filters.length >= 4
      ? ok(`필터 버튼 ${filters.length}개`)
      : fail("필터", `${filters.length}개`);
  } catch (e) {
    fail("KB 산출물", e.message);
  }

  // ═══════════════════════════════════════
  // T9: KB — KB 검색 탭 + 건강도 위젯
  // ═══════════════════════════════════════
  console.log("\n[T9] KB 검색 + 건강도 위젯");
  try {
    await page.goto(`${BASE}/kb/search`, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForTimeout(1000);

    // KB 검색 탭 클릭
    const searchTab = await page.$("text=KB 검색");
    if (searchTab) await searchTab.click();
    await page.waitForTimeout(2000);

    // 검색 입력
    const searchInput = await page.$('input[placeholder*="검색"]');
    searchInput ? ok("KB 검색 입력 존재") : fail("검색 입력", "미발견");

    // 영역 필터 (콘텐츠/발주기관/경쟁사/교훈/역량)
    const areaFilters = await page.$$("text=/콘텐츠|발주기관|경쟁사|교훈|역량/");
    areaFilters.length >= 4
      ? ok(`영역 필터 ${areaFilters.length}개`)
      : fail("영역 필터", `${areaFilters.length}개`);

    // KB 건강도 위젯 (Phase D 구현)
    const healthWidget = await page.$("text=KB 건강도");
    healthWidget
      ? ok("KB 건강도 위젯 표시")
      : fail("KB 건강도 위젯", "미표시 (API 연결 실패 가능)");
  } catch (e) {
    fail("KB 검색", e.message);
  }

  // ═══════════════════════════════════════
  // T10: KB 하위 페이지 라우팅
  // ═══════════════════════════════════════
  console.log("\n[T10] KB 하위 페이지");
  const kbPages = [
    { path: "/kb/content", name: "콘텐츠 라이브러리", check: "콘텐츠 라이브러리" },
    { path: "/kb/clients", name: "발주기관 DB", check: "발주기관" },
    { path: "/kb/competitors", name: "경쟁사 DB", check: "경쟁사" },
    { path: "/kb/lessons", name: "교훈 아카이브", check: "교훈" },
    { path: "/kb/labor-rates", name: "노임단가", check: "노임단가" },
    { path: "/kb/market-prices", name: "시장 가격", check: "시장" },
    { path: "/kb/qa", name: "Q&A", check: "Q&A" },
  ];

  for (const pg of kbPages) {
    try {
      await page.goto(`${BASE}${pg.path}`, { waitUntil: "networkidle", timeout: 10000 });
      await page.waitForTimeout(1000);
      const url = page.url();
      // 로그인 페이지로 리다이렉트되지 않았으면 성공
      !url.includes("/login")
        ? ok(`${pg.name} (${pg.path}) 로드`)
        : fail(`${pg.name}`, "로그인 리다이렉트");
    } catch (e) {
      fail(`${pg.name}`, e.message);
    }
  }

  // ═══════════════════════════════════════
  // T11: 다크 모드 토글
  // ═══════════════════════════════════════
  console.log("\n[T11] 다크 모드");
  try {
    await page.goto(`${BASE}/dashboard`, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForTimeout(1500);

    // 온보딩 모달 닫기
    const skipBtn = await page.$("text=건너뛰기");
    if (skipBtn) await skipBtn.click();
    await page.waitForTimeout(500);

    const darkToggle = await page.$("text=다크 모드");
    if (darkToggle) {
      await darkToggle.click();
      await page.waitForTimeout(500);
      ok("다크 모드 토글 클릭");
    } else {
      fail("다크 모드", "토글 미발견");
    }
  } catch (e) {
    fail("다크 모드", e.message);
  }

  // ═══════════════════════════════════════
  // T12: 알림 벨 + 로그아웃 존재
  // ═══════════════════════════════════════
  console.log("\n[T12] 공통 UI 요소");
  try {
    await page.goto(`${BASE}/dashboard`, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForTimeout(1500);

    const skipBtn = await page.$("text=건너뛰기");
    if (skipBtn) await skipBtn.click();
    await page.waitForTimeout(500);

    const logoutBtn = await page.$("text=로그아웃");
    logoutBtn ? ok("로그아웃 버튼 존재") : fail("로그아웃", "미발견");

    const userEmail = await page.$(`text=${CREDS.email}`);
    userEmail ? ok("사용자 이메일 표시") : fail("사용자 이메일", "미표시");
  } catch (e) {
    fail("공통 UI", e.message);
  }

  // ═══════════════════════════════════════
  // 결과 요약
  // ═══════════════════════════════════════
  await browser.close();

  console.log("\n" + "═".repeat(50));
  console.log(`📊 테스트 결과: ${passed} passed, ${failed} failed (총 ${passed + failed})`);
  console.log("═".repeat(50));

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
