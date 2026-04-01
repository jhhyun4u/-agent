import { test, expect } from "@playwright/test";

test.describe("Smoke Tests — 주요 페이지 렌더링", () => {
  test("로그인 페이지 → DEV 모드에서 /proposals 리다이렉트", async ({
    page,
  }) => {
    await page.goto("/login");
    // DEV 모드: /login → /proposals 리다이렉트 (middleware)
    await expect(page).toHaveURL(/proposals/);
  });

  test("대시보드 페이지 로드", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/dashboard/);
  });

  test("제안서 목록 페이지 로드", async ({ page }) => {
    await page.goto("/proposals");
    await expect(page).toHaveURL(/proposals/);
  });

  test("공고 목록 페이지 로드", async ({ page }) => {
    await page.goto("/monitoring");
    await expect(page).toHaveURL(/monitoring/);
  });

  test("분석 페이지 로드", async ({ page }) => {
    await page.goto("/analytics");
    await expect(page).toHaveURL(/analytics/);
  });

  test("KB 콘텐츠 페이지 로드", async ({ page }) => {
    await page.goto("/kb/content");
    await expect(page).toHaveURL(/kb\/content/);
  });
});

test.describe("네비게이션", () => {
  test("/ 루트 페이지 로드", async ({ page }) => {
    await page.goto("/");
    // DEV 모드: 인증 우회되므로 루트 페이지 그대로 렌더링
    await expect(page).toHaveURL("http://localhost:3000/");
  });

  test("존재하지 않는 경로 → 404 또는 그대로 로드", async ({ page }) => {
    const resp = await page.goto("/nonexistent-page-xyz");
    // Next.js가 404 반환하거나, DEV 모드에서 그대로 통과
    expect(resp?.status()).toBeLessThanOrEqual(404);
  });
});
