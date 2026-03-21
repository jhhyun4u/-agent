import { test, expect } from "@playwright/test";

test.describe("Smoke Tests — 주요 페이지 렌더링", () => {
  test("로그인 페이지 로드", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h2")).toContainText("로그인");
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
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
    await page.goto("/bids");
    await expect(page).toHaveURL(/bids/);
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

test.describe("로그인 폼 인터랙션", () => {
  test("빈 폼 제출 시 브라우저 유효성 검사", async ({ page }) => {
    await page.goto("/login");
    const emailInput = page.locator('input[type="email"]');
    // HTML required 속성으로 인해 빈 상태에서 submit 불가
    await expect(emailInput).toHaveAttribute("required", "");
  });

  test("이메일 입력 후 비밀번호 없이 제출 불가", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "test@tenopa.com");
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toHaveAttribute("required", "");
  });
});

test.describe("네비게이션", () => {
  test("/ 루트 → 로그인 리다이렉트 (미인증)", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/login/);
  });

  test("존재하지 않는 경로 → 로그인으로 리다이렉트 (미인증)", async ({ page }) => {
    await page.goto("/nonexistent-page-xyz");
    // 미들웨어가 비공개 경로를 /login으로 리다이렉트
    await expect(page).toHaveURL(/login/);
  });
});
