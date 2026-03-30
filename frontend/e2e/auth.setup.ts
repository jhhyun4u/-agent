import { test as setup, expect } from "@playwright/test";
import path from "path";

const STORAGE_STATE = path.join(__dirname, ".auth/user.json");

/**
 * 인증 셋업 — UI 로그인 후 storageState 저장
 *
 * 환경 변수:
 *   E2E_USER_EMAIL    테스트 계정 이메일
 *   E2E_USER_PASSWORD 테스트 계정 비밀번호
 *
 * .env.local 또는 환경변수로 설정 필요
 */
setup("로그인 후 인증 상태 저장", async ({ page }) => {
  const email = process.env.E2E_USER_EMAIL;
  const password = process.env.E2E_USER_PASSWORD;

  if (!email || !password) {
    console.warn(
      "⚠️  E2E_USER_EMAIL / E2E_USER_PASSWORD 미설정 — 인증 테스트 스킵"
    );
    // 빈 storageState 저장하여 authenticated 프로젝트가 에러 없이 실행되도록 함
    await page.context().storageState({ path: STORAGE_STATE });
    return;
  }

  // 1) 로그인 페이지 이동
  await page.goto("/login");
  await expect(page.locator("h2")).toContainText("로그인");

  // 2) 이메일·비밀번호 입력
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);

  // 3) 로그인 버튼 클릭
  await page.locator('button[type="submit"]').click();

  // 4) 로그인 성공 대기 — /proposals 또는 /change-password로 이동
  await page.waitForURL(/\/(proposals|change-password|dashboard)/, {
    timeout: 30000,
  });

  // 5) 인증 상태(쿠키 포함) 저장
  await page.context().storageState({ path: STORAGE_STATE });
});
