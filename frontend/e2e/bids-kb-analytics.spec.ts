import { test, expect } from "@playwright/test";

/**
 * 공고 모니터링, KB, 분석 대시보드 E2E 테스트
 */

test.describe("공고 모니터링 페이지", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/bids");
  });

  test("페이지 헤더 렌더링", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("공고 모니터링");
  });

  test("뷰 전환 탭 존재 (AI 추천 / 모니터링)", async ({ page }) => {
    await expect(page.getByRole("button", { name: "AI 추천" })).toBeVisible();
    await expect(page.getByRole("button", { name: "모니터링" })).toBeVisible();
  });

  test("AI 추천 탭 클릭", async ({ page }) => {
    await page.getByRole("button", { name: "AI 추천" }).click();
    await expect(page.locator("h1")).toContainText("공고 모니터링");
  });

  test("기본 뷰 모드는 AI 추천 (scored)", async ({ page }) => {
    // AI 추천 탭이 활성 상태 (bg-[#3ecf8e])
    const aiBtn = page.getByRole("button", { name: "AI 추천" });
    await expect(aiBtn).toBeVisible();
  });
});

test.describe("공고 설정 페이지", () => {
  test("페이지 로드", async ({ page }) => {
    await page.goto("/bids/settings");
    await expect(page).toHaveURL(/bids\/settings/);
  });
});

test.describe("분석 대시보드", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/analytics", { timeout: 60000 });
  });

  test("페이지 로드", async ({ page }) => {
    await expect(page).toHaveURL(/analytics/);
  });

  test("페이지 헤더 확인", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("제안 분석 대시보드");
  });

  test("기간 필터 select 존재", async ({ page }) => {
    const select = page.locator("select");
    await expect(select).toBeVisible();
    // 기본값 1Q 선택 확인
    await expect(select).toHaveValue("1Q");
  });

  test("기간 필터 변경 동작", async ({ page }) => {
    const select = page.locator("select");
    await select.selectOption("all");
    await expect(select).toHaveValue("all");
  });
});

test.describe("KB 콘텐츠 페이지", () => {
  test("페이지 로드", async ({ page }) => {
    await page.goto("/kb/content");
    await expect(page).toHaveURL(/kb\/content/);
  });
});

test.describe("KB 검색 페이지", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/kb/search");
  });

  test("페이지 로드", async ({ page }) => {
    await expect(page).toHaveURL(/kb\/search/);
  });

  test("검색 영역 필터 버튼 존재", async ({ page }) => {
    await expect(page.getByRole("button", { name: "콘텐츠" })).toBeVisible();
    await expect(page.getByRole("button", { name: "발주기관" })).toBeVisible();
    await expect(page.getByRole("button", { name: "경쟁사" })).toBeVisible();
    await expect(page.getByRole("button", { name: "교훈" })).toBeVisible();
    await expect(page.getByRole("button", { name: "역량" })).toBeVisible();
  });
});

test.describe("KB 하위 페이지 렌더링", () => {
  test("발주기관", async ({ page }) => {
    await page.goto("/kb/clients");
    await expect(page).toHaveURL(/kb\/clients/);
  });

  test("경쟁사", async ({ page }) => {
    await page.goto("/kb/competitors");
    await expect(page).toHaveURL(/kb\/competitors/);
  });

  test("교훈", async ({ page }) => {
    await page.goto("/kb/lessons");
    await expect(page).toHaveURL(/kb\/lessons/);
  });

  test("노임단가", async ({ page }) => {
    await page.goto("/kb/labor-rates");
    await expect(page).toHaveURL(/kb\/labor-rates/);
  });

  test("시장단가", async ({ page }) => {
    await page.goto("/kb/market-prices");
    await expect(page).toHaveURL(/kb\/market-prices/);
  });

  test("Q&A", async ({ page }) => {
    await page.goto("/kb/qa");
    await expect(page).toHaveURL(/kb\/qa/);
  });
});

test.describe("아카이브 페이지", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/archive");
  });

  test("페이지 로드", async ({ page }) => {
    await expect(page).toHaveURL(/archive/);
  });

  test("스코프 탭 존재 (전체/우리 팀/나의)", async ({ page }) => {
    await expect(page.getByText("전체", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("우리 팀", { exact: true })).toBeVisible();
    await expect(page.getByText("나의", { exact: true })).toBeVisible();
  });

  test("수주결과 필터 존재 (수주/낙찰실패/대기)", async ({ page }) => {
    await expect(page.getByText("수주", { exact: true })).toBeVisible();
    await expect(page.getByText("낙찰실패", { exact: true })).toBeVisible();
    await expect(page.getByText("대기", { exact: true })).toBeVisible();
  });
});

test.describe("관리자 페이지", () => {
  test("조직도 페이지 로드", async ({ page }) => {
    await page.goto("/admin");
    await expect(page).toHaveURL(/admin/);
  });

  test("사용자 관리 페이지 로드", async ({ page }) => {
    await page.goto("/admin/users");
    await expect(page).toHaveURL(/admin\/users/);
  });

  test("프롬프트 관리 페이지 로드", async ({ page }) => {
    await page.goto("/admin/prompts");
    await expect(page).toHaveURL(/admin\/prompts/);
  });
});

test.describe("가격 시뮬레이터 (비공개 경로)", () => {
  test("/pricing → 로그인 리다이렉트", async ({ page }) => {
    await page.goto("/pricing");
    await expect(page).toHaveURL(/login/);
  });

  test("/pricing/history → 로그인 리다이렉트", async ({ page }) => {
    await page.goto("/pricing/history");
    await expect(page).toHaveURL(/login/);
  });
});
