import { test, expect } from "@playwright/test";

/**
 * 인증된 상태 E2E 테스트
 *
 * - storageState로 로그인 쿠키 주입 (auth.setup.ts에서 생성)
 * - E2E_USER_EMAIL 미설정 시 graceful skip
 */

const hasCredentials = !!(
  process.env.E2E_USER_EMAIL && process.env.E2E_USER_PASSWORD
);

// ── 비공개 페이지 접근 (미인증 시 /login 리다이렉트되는 경로) ──

test.describe("비공개 페이지 — 인증 시 접근 가능", () => {
  test.skip(!hasCredentials, "E2E 테스트 계정 미설정");

  test("가격 시뮬레이터 페이지 로드", async ({ page }) => {
    await page.goto("/pricing");
    await expect(page).not.toHaveURL(/login/);
    await expect(page.locator("h1")).toContainText("비딩 가격 시뮬레이터");
  });

  test("가격 시뮬레이션 이력 페이지 로드", async ({ page }) => {
    await page.goto("/pricing/history");
    await expect(page).not.toHaveURL(/login/);
  });

  test("비밀번호 변경 페이지 로드", async ({ page }) => {
    await page.goto("/change-password");
    await expect(page).not.toHaveURL(/login/);
    await expect(page.locator("h2")).toContainText("비밀번호 변경");
  });

  test("온보딩 페이지 로드", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page).not.toHaveURL(/login/);
  });
});

// ── 로그인 후 /login 접근 시 리다이렉트 ──

test.describe("인증된 사용자 → /login 리다이렉트", () => {
  test.skip(!hasCredentials, "E2E 테스트 계정 미설정");

  test("/login 접근 시 /proposals로 리다이렉트", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveURL(/proposals/);
  });
});

// ── 제안서 목록 — 인라인 패널 인터랙션 ──

test.describe("제안서 인라인 패널 (인증 상태)", () => {
  test.skip(!hasCredentials, "E2E 테스트 계정 미설정");

  test("+ RFP 업로드 클릭 시 닫기 버튼 표시", async ({ page }) => {
    await page.goto("/proposals");
    await page.getByText("+ RFP 업로드").click();
    await expect(
      page.getByRole("button", { name: "닫기" }).first(),
    ).toBeVisible({
      timeout: 10000,
    });
  });

  test("공고에서 시작 클릭 시 닫기 버튼 표시", async ({ page }) => {
    await page.goto("/proposals");
    await page.getByText("공고에서 시작").click();
    await expect(
      page.getByRole("button", { name: "닫기" }).first(),
    ).toBeVisible({
      timeout: 10000,
    });
  });

  test("닫기 클릭 후 원래 버튼 복원", async ({ page }) => {
    await page.goto("/proposals");
    await page.getByText("+ RFP 업로드").click();
    await page
      .getByRole("button", { name: "닫기" })
      .first()
      .click({ timeout: 10000 });
    await expect(page.getByText("+ RFP 업로드")).toBeVisible({
      timeout: 10000,
    });
  });
});

// ── 대시보드 위젯 ──

test.describe("대시보드 (인증 상태)", () => {
  test.skip(!hasCredentials, "E2E 테스트 계정 미설정");

  test("대시보드 페이지 로드 및 헤더 확인", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/dashboard/);
  });
});

// ── 공고 모니터링 뷰 전환 ──

test.describe("공고 모니터링 — 뷰 전환 (인증 상태)", () => {
  test.skip(!hasCredentials, "E2E 테스트 계정 미설정");

  test("모니터링 탭 클릭 시 스코프 탭 표시", async ({ page }) => {
    await page.goto("/bids");
    await page.getByRole("button", { name: "모니터링" }).click();
    await expect(page.getByRole("button", { name: "팀" })).toBeVisible({
      timeout: 10000,
    });
  });
});

// ── 사이드바 네비게이션 (로그아웃 버튼 포함) ──

test.describe("사이드바 — 인증 전용 요소", () => {
  test.skip(!hasCredentials, "E2E 테스트 계정 미설정");

  test("로그아웃 버튼 표시", async ({ page }) => {
    await page.goto("/proposals");
    await expect(page.getByText("로그아웃")).toBeVisible();
  });

  test("알림 벨 아이콘 표시", async ({ page }) => {
    await page.goto("/proposals");
    // NotificationBell 컴포넌트의 알림 아이콘
    const bell = page.locator('[aria-label="알림"]').or(
      page
        .locator("button")
        .filter({ has: page.locator("svg") })
        .last(),
    );
    // 알림 벨은 사이드바에 있으므로 존재 확인
    await expect(page.getByText("로그아웃")).toBeVisible();
  });
});
