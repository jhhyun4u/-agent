import { test } from "@playwright/test";

test("공고 모니터링 — 전체 페이지", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/monitoring", { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: "test-results/monitoring-01-full.png", fullPage: false });
});

test("공고 모니터링 — 필터 영역", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/monitoring", { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2000);
  // 스코프 탭 영역 스크린샷
  await page.screenshot({ path: "test-results/monitoring-02-filters.png", fullPage: false });
});

test("공고 모니터링 — 사이드바 확인", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/monitoring", { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2000);
  // 사이드바 영역만 캡처
  const sidebar = page.locator("nav").first();
  if (await sidebar.isVisible()) {
    await sidebar.screenshot({ path: "test-results/monitoring-03-sidebar.png" });
  } else {
    await page.screenshot({ path: "test-results/monitoring-03-sidebar.png", clip: { x: 0, y: 0, width: 260, height: 900 } });
  }
});
