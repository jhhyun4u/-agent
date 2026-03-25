import { test, expect } from "@playwright/test";

/**
 * 로그인·인증 플로우 테스트
 */

test.describe("로그인 폼 UI", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
  });

  test("로그인 폼 구성요소 전부 렌더링", async ({ page }) => {
    await expect(page.locator("h2")).toContainText("로그인");
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test("이메일 필드에 입력 가능", async ({ page }) => {
    const email = page.locator('input[type="email"]');
    await email.fill("test@tenopa.com");
    await expect(email).toHaveValue("test@tenopa.com");
  });

  test("비밀번호 필드에 입력 가능", async ({ page }) => {
    const pw = page.locator('input[type="password"]');
    await pw.fill("password123");
    await expect(pw).toHaveValue("password123");
  });

  test("이메일 필드는 required 속성 보유", async ({ page }) => {
    await expect(page.locator('input[type="email"]')).toHaveAttribute("required", "");
  });

  test("비밀번호 필드는 required 속성 보유", async ({ page }) => {
    await expect(page.locator('input[type="password"]')).toHaveAttribute("required", "");
  });
});

test.describe("비밀번호 변경 (비공개 경로)", () => {
  test("/change-password → 로그인 리다이렉트", async ({ page }) => {
    await page.goto("/change-password");
    // PUBLIC_PATHS에 없으므로 미인증 시 /login 리다이렉트
    await expect(page).toHaveURL(/login/);
  });
});

test.describe("인증 리다이렉트", () => {
  test("/ 루트 접근 시 /login 리다이렉트", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/login/);
  });

  test("존재하지 않는 경로 → /login 리다이렉트", async ({ page }) => {
    await page.goto("/this-page-does-not-exist-xyz");
    await expect(page).toHaveURL(/login/);
  });

  test("onboarding 페이지 (비공개) → /login 리다이렉트", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page).toHaveURL(/login/);
  });
});
