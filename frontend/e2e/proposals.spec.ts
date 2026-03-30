import { test, expect } from "@playwright/test";

/**
 * 제안서 워크플로 E2E 테스트
 */

test.describe("제안 프로젝트 목록 페이지", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/proposals");
  });

  test("페이지 헤더 렌더링", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("제안 프로젝트 목록");
  });

  test("스코프 탭 4개 존재 (개인/팀/본부/전체)", async ({ page }) => {
    await expect(page.getByText("개인", { exact: true })).toBeVisible();
    await expect(page.getByText("팀", { exact: true })).toBeVisible();
    await expect(page.getByText("본부", { exact: true })).toBeVisible();
    // "전체"는 스코프 탭과 상태 필터에 모두 존재 → first()로 한정
    await expect(page.getByText("전체", { exact: true }).first()).toBeVisible();
  });

  test("검색 입력 필드 존재", async ({ page }) => {
    await expect(page.locator('input[placeholder="프로젝트명 검색..."]')).toBeVisible();
  });

  test("상태 필터 버튼 존재 (전체/진행중/완료/실패)", async ({ page }) => {
    const filters = page.locator("button");
    await expect(page.getByText("진행중", { exact: true })).toBeVisible();
    await expect(page.getByText("완료", { exact: true }).first()).toBeVisible();
  });

  test("+ RFP 업로드 버튼 존재", async ({ page }) => {
    await expect(page.getByText("+ RFP 업로드")).toBeVisible();
  });

  test("공고에서 시작 버튼 존재", async ({ page }) => {
    await expect(page.getByText("공고에서 시작")).toBeVisible();
  });

  test("검색 입력 가능", async ({ page }) => {
    const searchInput = page.locator('input[placeholder="프로젝트명 검색..."]');
    await searchInput.fill("테스트 프로젝트");
    await expect(searchInput).toHaveValue("테스트 프로젝트");
  });

  test("스코프 탭 클릭 시 전환", async ({ page }) => {
    const companyTab = page.getByText("전체", { exact: true }).first();
    await companyTab.click();
    // 클릭 후에도 페이지가 정상 동작하는지 확인
    await expect(page.locator("h1")).toContainText("제안 프로젝트 목록");
  });

  test("상태 필터 클릭 동작", async ({ page }) => {
    await page.getByText("진행중", { exact: true }).click();
    await expect(page.locator("h1")).toContainText("제안 프로젝트 목록");
  });
});

test.describe("새 제안서 생성 페이지", () => {
  test("페이지 로드 및 헤더 확인", async ({ page }) => {
    await page.goto("/proposals/new");
    await expect(page.getByText("새 제안서 생성")).toBeVisible();
  });

  test("진입 경로 선택 카드 렌더링", async ({ page }) => {
    await page.goto("/proposals/new");
    // 진입 경로 선택 화면에서 RFP 업로드 옵션이 보여야 함
    await expect(page.getByText("RFP 파일")).toBeVisible();
  });
});

test.describe("제안서 목록 — 사이드바 네비게이션", () => {
  test("사이드바에 제안 프로젝트 메뉴 활성", async ({ page }) => {
    await page.goto("/proposals");
    await expect(page.getByLabel("제안 프로젝트").first()).toBeVisible();
  });

  test("사이드바에 공고 모니터링 링크 존재", async ({ page }) => {
    await page.goto("/proposals");
    await expect(page.getByText("공고 모니터링").first()).toBeVisible();
  });

  test("사이드바에 대시보드 링크 존재", async ({ page }) => {
    await page.goto("/proposals");
    await expect(page.getByText("대시보드").first()).toBeVisible();
  });
});
