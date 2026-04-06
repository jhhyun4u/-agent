import { test, expect } from "@playwright/test";

/**
 * 로그인·인증 플로우 테스트
 *
 * DEV 모드 (NODE_ENV=development): /login → /proposals 리다이렉트
 * 따라서 로그인 폼 UI 테스트는 skip, 리다이렉트 동작만 검증.
 */

test.describe("로그인 리다이렉트 (DEV 모드)", () => {
  test("/login → /proposals 리다이렉트", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveURL(/proposals/);
  });
});

test.describe("비공개 경로 (DEV 모드 — 인증 우회)", () => {
  test("/change-password → DEV에서 그대로 로드", async ({ page }) => {
    await page.goto("/change-password");
    // DEV 모드에서는 인증이 우회되므로 리다이렉트 없음
    await expect(page).toHaveURL(/change-password/);
  });

  test("/ 루트 페이지 로드", async ({ page }) => {
    await page.goto("/");
    // DEV 모드에서는 루트 그대로 렌더링
    await expect(page).toHaveURL("http://localhost:3000/");
  });
});
