import { test, expect } from "@playwright/test";

/**
 * 추가 페이지 렌더링 테스트 — smoke.spec.ts 에서 다루지 않는 페이지
 */

test.describe("추가 페이지 렌더링", () => {
  test("비밀번호 변경 페이지", async ({ page }) => {
    await page.goto("/change-password");
    // DEV 모드에서는 인증 우회 → 그대로 로드
    await expect(page).toHaveURL(/change-password/);
  });

  test("새 제안서 생성 페이지", async ({ page }) => {
    await page.goto("/proposals/new");
    await expect(page).toHaveURL(/proposals\/new/);
  });

  test("아카이브 페이지", async ({ page }) => {
    await page.goto("/archive");
    await expect(page).toHaveURL(/archive/);
  });

  test("관리자 페이지", async ({ page }) => {
    await page.goto("/admin");
    await expect(page).toHaveURL(/admin/);
  });

  test("사용자 관리 페이지", async ({ page }) => {
    await page.goto("/admin/users");
    await expect(page).toHaveURL(/admin\/users/);
  });

  test("가격 시뮬레이터 페이지", async ({ page }) => {
    await page.goto("/pricing");
    // DEV 모드에서는 인증 우회 → 그대로 로드
    await expect(page).toHaveURL(/pricing/);
  });

  test("가격 시뮬레이션 이력 페이지", async ({ page }) => {
    await page.goto("/pricing/history");
    await expect(page).toHaveURL(/pricing\/history/);
  });

  test("KB 검색 페이지", async ({ page }) => {
    await page.goto("/kb/search");
    await expect(page).toHaveURL(/kb\/search/);
  });

  test("KB 발주기관 페이지", async ({ page }) => {
    await page.goto("/kb/clients");
    await expect(page).toHaveURL(/kb\/clients/);
  });

  test("KB 경쟁사 페이지", async ({ page }) => {
    await page.goto("/kb/competitors");
    await expect(page).toHaveURL(/kb\/competitors/);
  });

  test("KB 교훈 페이지", async ({ page }) => {
    await page.goto("/kb/lessons");
    await expect(page).toHaveURL(/kb\/lessons/);
  });

  test("KB 노임단가 페이지", async ({ page }) => {
    await page.goto("/kb/labor-rates");
    await expect(page).toHaveURL(/kb\/labor-rates/);
  });

  test("KB 시장단가 페이지", async ({ page }) => {
    await page.goto("/kb/market-prices");
    await expect(page).toHaveURL(/kb\/market-prices/);
  });

  test("KB Q&A 페이지", async ({ page }) => {
    await page.goto("/kb/qa");
    await expect(page).toHaveURL(/kb\/qa/);
  });

  test("리소스 페이지", async ({ page }) => {
    await page.goto("/resources");
    await expect(page).toHaveURL(/resources/);
  });

  test("공고 설정 페이지", async ({ page }) => {
    await page.goto("/bids/settings");
    await expect(page).toHaveURL(/bids\/settings/);
  });
});
